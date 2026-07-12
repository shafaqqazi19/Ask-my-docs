"""BM25 lexical retriever, loaded from a prebuilt pickle index."""
from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScoredChunkId:
    chunk_id: str
    score: float


class BM25Retriever:
    def __init__(self, index_path: Path):
        with open(index_path, "rb") as f:
            data = pickle.load(f)
        self.bm25 = data["bm25"]
        self.chunk_ids: list[str] = data["chunk_ids"]

    def search(self, query: str, top_k: int = 25) -> list[ScoredChunkId]:
        tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)
        ranked_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [ScoredChunkId(chunk_id=self.chunk_ids[i], score=float(scores[i])) for i in ranked_idx]
