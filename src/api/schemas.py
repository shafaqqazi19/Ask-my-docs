from __future__ import annotations

from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str


class EvidenceItem(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    score: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    is_fully_grounded: bool
    was_rejected: bool
    hallucinated_citations: list[str]
    evidence: list[EvidenceItem]
    latency_ms: float


class UploadResponse(BaseModel):
    success: bool
    message: str
    files_accepted: int
    total_documents: int
    total_chunks: int
