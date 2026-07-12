"""Build the BM25 lexical index and the FAISS dense vector index from chunks."""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from src.ingestion.chunker import Chunk


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def build_bm25_index(chunks: list[Chunk], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_tokens = [_tokenize(c.text) for c in chunks]
    bm25 = BM25Okapi(corpus_tokens)

    with open(output_path, "wb") as f:
        pickle.dump({"bm25": bm25, "chunk_ids": [c.chunk_id for c in chunks]}, f)


def build_vector_index(
    chunks: list[Chunk],
    faiss_path: Path,
    metadata_path: Path,
    embedding_model_name: str,
) -> None:
    faiss_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    model = SentenceTransformer(embedding_model_name)
    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    embeddings = np.asarray(embeddings, dtype="float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine sim via normalized inner product
    index.add(embeddings)
    faiss.write_index(index, str(faiss_path))

    with open(metadata_path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps({
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "text": c.text,
                "position": c.position,
            }) + "\n")


def build_all_indexes(
    chunks: list[Chunk],
    bm25_index_path: Path,
    faiss_index_path: Path,
    metadata_path: Path,
    embedding_model_name: str,
) -> None:
    build_bm25_index(chunks, bm25_index_path)
    build_vector_index(chunks, faiss_index_path, metadata_path, embedding_model_name)
