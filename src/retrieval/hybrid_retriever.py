"""Hybrid retriever: fuses BM25 + vector search via Reciprocal Rank Fusion (RRF),
then re-ranks the fused candidate set with a cross-encoder.
"""
from __future__ import annotations

from src.retrieval.bm25_retriever import BM25Retriever
from src.retrieval.reranker import CrossEncoderReranker, RerankedChunk
from src.retrieval.types import Evidence
from src.retrieval.vector_retriever import VectorRetriever


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> dict[str, float]:
    """Standard RRF: score(d) = sum over lists of 1 / (k + rank_in_list)."""
    fused: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, chunk_id in enumerate(ranked):
            fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
    return fused


class HybridRetriever:
    def __init__(
        self,
        bm25: BM25Retriever,
        vector: VectorRetriever,
        reranker: CrossEncoderReranker,
    ):
        self.bm25 = bm25
        self.vector = vector
        self.reranker = reranker

    def retrieve(
        self,
        query: str,
        bm25_top_k: int = 25,
        vector_top_k: int = 25,
        rerank_top_k: int = 5,
    ) -> list[Evidence]:
        bm25_hits = self.bm25.search(query, top_k=bm25_top_k)
        vector_hits = self.vector.search(query, top_k=vector_top_k)

        fused_scores = reciprocal_rank_fusion(
            [[h.chunk_id for h in bm25_hits], [h.chunk_id for h in vector_hits]]
        )
        fused_ranked_ids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)

        # Build candidate (chunk_id, text, doc_id) tuples for reranking.
        candidates = []
        for cid in fused_ranked_ids:
            try:
                text = self.vector.get_text(cid)
                doc_id = self.vector.get_doc_id(cid)
            except KeyError:
                continue
            candidates.append((cid, text, doc_id))

        reranked: list[RerankedChunk] = self.reranker.rerank(query, candidates, top_k=rerank_top_k)

        return [
            Evidence(chunk_id=r.chunk_id, doc_id=r.doc_id, text=r.text, score=r.rerank_score)
            for r in reranked
        ]
