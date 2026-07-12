"""Database engine and session management.

Uses a plain sync SQLAlchemy engine. FastAPI runs sync `def` route handlers in a
threadpool automatically, so this doesn't block the event loop despite being sync
- and sync keeps the logging path simple and easy to reason about / test.
"""
from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings
from src.db.models import Base

_engine = None
_SessionLocal: sessionmaker | None = None


def is_configured() -> bool:
    """Return True if DATABASE_URL is set and non-empty."""
    return bool(settings.database_url)


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)
    return _SessionLocal


def init_db() -> None:
    """Create tables if they don't exist. For anything beyond a demo/small
    deployment, replace this with proper Alembic migrations."""
    Base.metadata.create_all(bind=get_engine())


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session: Session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
