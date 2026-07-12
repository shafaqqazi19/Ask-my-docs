"""Cross-encoder re-ranker: jointly scores (query, passage) pairs for precision."""
from __future__ import annotations

from dataclasses import dataclass

from sentence_transformers import CrossEncoder


@dataclass
class RerankedChunk:
    chunk_id: str
    text: str
    doc_id: str
    rerank_score: float


class CrossEncoderReranker:
    def __init__(self, model_name: str):
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        candidates: list[tuple[str, str, str]],  # (chunk_id, text, doc_id)
        top_k: int = 5,
    ) -> list[RerankedChunk]:
        if not candidates:
            return []

        pairs = [(query, text) for _, text, _ in candidates]
        scores = self.model.predict(pairs)

        scored = [
            RerankedChunk(chunk_id=cid, text=text, doc_id=doc_id, rerank_score=float(score))
            for (cid, text, doc_id), score in zip(candidates, scores)
        ]
        scored.sort(key=lambda c: c.rerank_score, reverse=True)
        return scored[:top_k]
