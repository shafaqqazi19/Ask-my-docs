"""SQLAlchemy models for the query log.

One row per POST /query request: the question, the retrieved evidence chunks,
the generated (post-citation-enforcement) answer, grounding verdict, and latency.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    # List of {"chunk_id": ..., "doc_id": ..., "score": ..., "text": ...} dicts.
    # Stored as JSON so it works identically on Postgres (JSONB-compatible) and
    # SQLite (used in tests) without a database-specific column type.
    retrieved_chunks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    is_fully_grounded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    was_rejected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hallucinated_citations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<QueryLog id={self.id} question={self.question[:40]!r} latency_ms={self.latency_ms:.1f}>"
