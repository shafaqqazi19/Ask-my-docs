"""Centralized configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _env_int(key: str, default: int) -> int:
    return int(os.getenv(key, default))


@dataclass(frozen=True)
class Settings:
    # Embeddings / reranker (local models, no key required)
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    reranker_model: str = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

    # Retrieval tuning
    bm25_top_k: int = field(default_factory=lambda: _env_int("BM25_TOP_K", 25))
    vector_top_k: int = field(default_factory=lambda: _env_int("VECTOR_TOP_K", 25))
    rerank_top_k: int = field(default_factory=lambda: _env_int("RERANK_TOP_K", 5))

    # Chunking
    chunk_size: int = field(default_factory=lambda: _env_int("CHUNK_SIZE", 800))
    chunk_overlap: int = field(default_factory=lambda: _env_int("CHUNK_OVERLAP", 120))

    # Citation policy: "strip" removes unsupported sentences, "reject" refuses the
    # whole answer if any sentence is unsupported.
    citation_policy: str = os.getenv("CITATION_POLICY", "strip")

    # Generation
    generation_max_chars: int = field(
        default_factory=lambda: _env_int("GENERATION_MAX_CHARS", 500)
    )

    # Query-log database (PostgreSQL in production; any SQLAlchemy URL works, e.g.
    # sqlite:///./local.db for quick local runs without Postgres installed).
    # No hardcoded credentials — must be set via DATABASE_URL env var.
    database_url: str = os.getenv("DATABASE_URL", "")
    log_queries: bool = os.getenv("LOG_QUERIES", "true").lower() in ("1", "true", "yes")

    # Origins allowed to call this API from a browser (the Next.js frontend).
    # Comma-separated in the env var, e.g. "http://localhost:3000,https://app.example.com"
    cors_allowed_origins: list[str] = field(
        default_factory=lambda: [
            o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
        ]
    )

    # Storage paths
    storage_dir: Path = Path(os.getenv("STORAGE_DIR", "storage"))
    bm25_index_path: Path = field(init=False)
    faiss_index_path: Path = field(init=False)
    metadata_path: Path = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "bm25_index_path", self.storage_dir / "bm25_index" / "bm25.pkl")
        object.__setattr__(self, "faiss_index_path", self.storage_dir / "faiss_index" / "index.faiss")
        object.__setattr__(self, "metadata_path", self.storage_dir / "faiss_index" / "chunks.jsonl")


settings = Settings()
