"""CLI: ingest raw documents into the hybrid (BM25 + FAISS) index.

Usage:
    python scripts/ingest_docs.py --input data/raw --output storage
"""
from __future__ import annotations

import argparse
from pathlib import Path

from src.config import settings
from src.ingestion.chunker import chunk_documents
from src.ingestion.indexer import build_all_indexes
from src.ingestion.loader import load_documents


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Directory of raw documents (pdf/md/txt)")
    parser.add_argument("--output", default="storage", help="Directory to write indexes into")
    args = parser.parse_args()

    output_dir = Path(args.output)
    bm25_path = output_dir / "bm25_index" / "bm25.pkl"
    faiss_path = output_dir / "faiss_index" / "index.faiss"
    metadata_path = output_dir / "faiss_index" / "chunks.jsonl"

    print(f"[1/3] Loading documents from {args.input} ...")
    docs = load_documents(args.input)
    print(f"      loaded {len(docs)} document(s)")

    print(f"[2/3] Chunking (size={settings.chunk_size}, overlap={settings.chunk_overlap}) ...")
    chunks = chunk_documents(docs, chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
    print(f"      produced {len(chunks)} chunk(s)")

    print(f"[3/3] Building BM25 + FAISS indexes with embedding model '{settings.embedding_model}' ...")
    build_all_indexes(
        chunks,
        bm25_index_path=bm25_path,
        faiss_index_path=faiss_path,
        metadata_path=metadata_path,
        embedding_model_name=settings.embedding_model,
    )
    print(f"Done. Indexes written to {output_dir}/")


if __name__ == "__main__":
    main()
