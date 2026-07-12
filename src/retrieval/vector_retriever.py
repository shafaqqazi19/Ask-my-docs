"""Dense vector retriever backed by a FAISS flat inner-product index."""
from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src.retrieval.bm25_retriever import ScoredChunkId


class VectorRetriever:
    def __init__(self, faiss_index_path: Path, metadata_path: Path, embedding_model_name: str):
        self.index = faiss.read_index(str(faiss_index_path))
        self.model = SentenceTransformer(embedding_model_name)

        self.chunk_ids: list[str] = []
        self.chunk_lookup: dict[str, dict] = {}
        with open(metadata_path, "r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                self.chunk_ids.append(record["chunk_id"])
                self.chunk_lookup[record["chunk_id"]] = record

    def search(self, query: str, top_k: int = 25) -> list[ScoredChunkId]:
        q_emb = self.model.encode([query], normalize_embeddings=True)
        q_emb = np.asarray(q_emb, dtype="float32")

        scores, idxs = self.index.search(q_emb, top_k)
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            results.append(ScoredChunkId(chunk_id=self.chunk_ids[idx], score=float(score)))
        return results

    def get_text(self, chunk_id: str) -> str:
        return self.chunk_lookup[chunk_id]["text"]

    def get_doc_id(self, chunk_id: str) -> str:
        return self.chunk_lookup[chunk_id]["doc_id"]
