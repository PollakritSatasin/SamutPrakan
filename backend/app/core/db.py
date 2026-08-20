from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.models.base import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
        return kwargs
    return {}


def reset_engine(*, url: str | None = None) -> None:
    """Dispose the cached engine (used by tests)."""
    global _engine, _SessionLocal
    if url is not None:
        settings.database_url = url
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


def init_db() -> None:
    from app.models.case import CaseRecord
    from app.models.session import TrainingSessionRecord

    Base.metadata.create_all(
        bind=get_engine(),
        tables=[CaseRecord.__table__, TrainingSessionRecord.__table__],
    )


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
