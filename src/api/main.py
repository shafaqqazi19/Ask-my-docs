from __future__ import annotations

import logging
import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.api.schemas import EvidenceItem, QueryRequest, QueryResponse, UploadResponse
from src.config import settings
from src.db.repository import log_query
from src.db.session import init_db, is_configured
from src.ingestion.chunker import chunk_documents
from src.ingestion.indexer import build_all_indexes
from src.ingestion.loader import load_documents
from src.pipeline import RagPipeline

logger = logging.getLogger("ask_my_docs.api")

SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt", ".docx", ".html", ".htm", ".csv"}
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB per file

_pipeline: RagPipeline | None = None
_pipeline_error: str | None = None


def get_pipeline() -> RagPipeline:
    global _pipeline, _pipeline_error
    if _pipeline is not None:
        return _pipeline
    if _pipeline_error:
        raise HTTPException(status_code=503, detail=_pipeline_error)
    try:
        _pipeline = RagPipeline()
        return _pipeline
    except FileNotFoundError as exc:
        _pipeline_error = (
            "Index files not found. Upload documents via /upload to build the index, "
            f"or run scripts/ingest_docs.py to build them manually. ({exc})"
        )
        raise HTTPException(status_code=503, detail=_pipeline_error) from exc
    except Exception as exc:
        _pipeline_error = f"Failed to initialize RAG pipeline: {exc}"
        raise HTTPException(status_code=503, detail=_pipeline_error) from exc


def reset_pipeline() -> None:
    global _pipeline, _pipeline_error
    _pipeline = None
    _pipeline_error = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_pipeline()
    except HTTPException:
        logger.warning("Pipeline initialization deferred — index files not yet available.")

    if settings.log_queries and is_configured():
        try:
            init_db()
        except Exception:
            logger.exception(
                "Could not initialize the query-log database at startup. "
                "The API will still serve requests; query logging will be skipped "
                "per-request until the database is reachable."
            )

    yield


app = FastAPI(title="Ask My Docs", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload", response_model=UploadResponse)
async def upload_files(files: list[UploadFile] = File(...)):
    raw_dir = Path(settings.storage_dir.parent / "data" / "raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    accepted = 0
    skipped = []

    for f in files:
        ext = Path(f.filename or "").suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            skipped.append(f"{f.filename} (unsupported extension)")
            continue

        if f.size and f.size > MAX_UPLOAD_SIZE_BYTES:
            skipped.append(f"{f.filename} (exceeds {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB limit)")
            continue

        safe_name = Path(f.filename or f"unnamed{ext}").name
        dest = raw_dir / safe_name
        try:
            with open(dest, "wb") as buffer:
                shutil.copyfileobj(f.file, buffer)
            accepted += 1
        except Exception as exc:
            skipped.append(f"{f.filename} ({exc!r})")
        finally:
            f.file.close()

    if accepted == 0:
        raise HTTPException(status_code=400, detail=f"No files were accepted. Skipped: {', '.join(skipped)}")

    docs = []
    chunks = []
    try:
        docs = load_documents(raw_dir)
        chunks = chunk_documents(docs, chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
        build_all_indexes(
            chunks,
            bm25_index_path=settings.bm25_index_path,
            faiss_index_path=settings.faiss_index_path,
            metadata_path=settings.metadata_path,
            embedding_model_name=settings.embedding_model,
        )
    except Exception as exc:
        logger.exception("Ingestion failed after upload")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    reset_pipeline()
    # Eagerly re-initialize so the next /query doesn't pay the ~60s model-load
    # penalty on the first request after re-indexing.
    get_pipeline()

    msg = f"Accepted {accepted} file(s)"
    if skipped:
        msg += f". Skipped: {', '.join(skipped)}"

    return UploadResponse(
        success=True,
        message=msg,
        files_accepted=accepted,
        total_documents=len(docs),
        total_chunks=len(chunks),
    )


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    pipeline = get_pipeline()

    start = time.perf_counter()
    result = pipeline.answer(request.question)
    latency_ms = (time.perf_counter() - start) * 1000

    verification = result.verification
    is_fully_grounded = verification.is_fully_grounded if verification else False
    was_rejected = verification.was_rejected if verification else False
    hallucinated_citations = verification.hallucinated_citations if verification else []

    evidence_items = [
        EvidenceItem(chunk_id=e.chunk_id, doc_id=e.doc_id, text=e.text, score=e.score)
        for e in result.evidence
    ]

    if settings.log_queries and is_configured():
        log_query(
            question=result.question,
            answer=result.answer,
            retrieved_chunks=[
                {"chunk_id": e.chunk_id, "doc_id": e.doc_id, "score": e.score, "text": e.text}
                for e in result.evidence
            ],
            is_fully_grounded=is_fully_grounded,
            was_rejected=was_rejected,
            hallucinated_citations=hallucinated_citations,
            latency_ms=latency_ms,
        )

    return QueryResponse(
        question=result.question,
        answer=result.answer,
        is_fully_grounded=is_fully_grounded,
        was_rejected=was_rejected,
        hallucinated_citations=hallucinated_citations,
        evidence=evidence_items,
        latency_ms=round(latency_ms, 2),
    )
