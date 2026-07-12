"""Tests the query-log DB layer against a throwaway SQLite file rather than a real
Postgres server (no DB server available in unit test environments / CI runners
without a postgres service container). The code path (SQLAlchemy Core/ORM) is
identical regardless of backend, so this validates the logic; the docker-compose
Postgres service is what's used in actual local/deployed runs.
"""
from __future__ import annotations

import os

import pytest

import src.db.session as db_session
from src.config import settings
from src.db.models import QueryLog
from src.db.repository import log_query


@pytest.fixture()
def sqlite_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_query_logs.db"
    monkeypatch_url = f"sqlite:///{db_path}"

    # settings is a frozen dataclass; bypass immutability for this test only.
    object.__setattr__(settings, "database_url", monkeypatch_url)

    # Force session.py to rebuild its cached engine/session factory against the
    # new URL instead of reusing whatever it cached from a previous test/import.
    db_session._engine = None
    db_session._SessionLocal = None

    db_session.init_db()
    yield db_path

    db_session._engine = None
    db_session._SessionLocal = None
    if db_path.exists():
        os.remove(db_path)


def test_log_query_persists_and_reads_back(sqlite_db):
    row_id = log_query(
        question="What is the uptime SLA?",
        answer="CloudNest commits to 99.9% monthly uptime [cloudnest_sla.pdf::chunk-0000].",
        retrieved_chunks=[
            {"chunk_id": "cloudnest_sla.pdf::chunk-0000", "doc_id": "cloudnest_sla.pdf",
             "score": 0.87, "text": "CloudNest commits to 99.9% monthly uptime..."},
        ],
        is_fully_grounded=True,
        was_rejected=False,
        hallucinated_citations=[],
        latency_ms=842.3,
    )
    assert row_id is not None

    Session = db_session.get_session_factory()
    with Session() as session:
        rows = session.query(QueryLog).all()
        assert len(rows) == 1
        row = rows[0]
        assert row.question == "What is the uptime SLA?"
        assert row.is_fully_grounded is True
        assert row.latency_ms == pytest.approx(842.3)
        assert row.retrieved_chunks[0]["chunk_id"] == "cloudnest_sla.pdf::chunk-0000"
        assert row.created_at is not None


def test_log_query_returns_none_on_db_failure(monkeypatch):
    # Point at an unreachable database; log_query must not raise.
    object.__setattr__(settings, "database_url", "postgresql+psycopg://bad:bad@localhost:1/doesnotexist")
    db_session._engine = None
    db_session._SessionLocal = None

    result = log_query(
        question="test", answer="test", retrieved_chunks=[],
        is_fully_grounded=True, was_rejected=False, hallucinated_citations=[], latency_ms=1.0,
    )
    assert result is None
