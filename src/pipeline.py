"""End-to-end RAG pipeline: hybrid retrieve -> rerank -> generate -> enforce citations."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.config import settings
from src.generation.citation_enforcer import CitationEnforcer, VerificationResult
from src.generation.generator import Generator
from src.retrieval.bm25_retriever import BM25Retriever
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.types import Evidence
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.vector_retriever import VectorRetriever


@dataclass
class RagResponse:
    question: str
    answer: str
    evidence: list[Evidence] = field(default_factory=list)
    verification: VerificationResult | None = None


class RagPipeline:
    def __init__(self):
        bm25 = BM25Retriever(settings.bm25_index_path)
        vector = VectorRetriever(settings.faiss_index_path, settings.metadata_path, settings.embedding_model)
        reranker = CrossEncoderReranker(settings.reranker_model)

        self.hybrid_retriever = HybridRetriever(bm25=bm25, vector=vector, reranker=reranker)
        self.generator = Generator(max_chars=settings.generation_max_chars)
        self.citation_enforcer = CitationEnforcer(policy=settings.citation_policy)

    def answer(self, question: str) -> RagResponse:
        evidence = self.hybrid_retriever.retrieve(
            question,
            bm25_top_k=settings.bm25_top_k,
            vector_top_k=settings.vector_top_k,
            rerank_top_k=settings.rerank_top_k,
        )

        raw_answer = self.generator.generate_answer(question, evidence)
        verification = self.citation_enforcer.verify(raw_answer, evidence, skip_sentence_check=True)

        return RagResponse(
            question=question,
            answer=verification.cleaned_answer,
            evidence=evidence,
            verification=verification,
        )
