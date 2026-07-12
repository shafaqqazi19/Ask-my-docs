"""Repository functions for persisting query logs.

Logging failures must never break the user-facing request: if the database is
down, we log a warning server-side and let the API response go out normally.
"""
from __future__ import annotations

import logging

from src.db.models import QueryLog
from src.db.session import session_scope

logger = logging.getLogger("ask_my_docs.query_log")


def log_query(
    question: str,
    answer: str,
    retrieved_chunks: list[dict],
    is_fully_grounded: bool,
    was_rejected: bool,
    hallucinated_citations: list[str],
    latency_ms: float,
) -> str | None:
    """Persist a query log row. Returns the row id, or None if logging failed."""
    try:
        with session_scope() as session:
            row = QueryLog(
                question=question,
                answer=answer,
                retrieved_chunks=retrieved_chunks,
                is_fully_grounded=is_fully_grounded,
                was_rejected=was_rejected,
                hallucinated_citations=hallucinated_citations,
                latency_ms=latency_ms,
            )
            session.add(row)
            session.flush()
            row_id = row.id
        return row_id
    except Exception:
        logger.exception("Failed to write query log to database; continuing without persisting it.")
        return None
