"""
Database engine and session management.

This module owns exactly two things: the SQLAlchemy `engine` (the
connection to the SQLite file) and `SessionLocal` (a factory for
per-request sessions). Nothing else in the codebase should construct an
engine or a session directly — everything goes through `get_db()` below,
so there is one consistent connection lifecycle for the whole app.
"""

from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import get_settings

settings = get_settings()

# `check_same_thread=False` is required for SQLite specifically: SQLite
# normally refuses to let a connection be used from a different thread
# than the one that created it, but FastAPI's dependency system can hand
# a session to request-handling code running on a different thread. Each
# request still gets its OWN session (see get_db below), so this is safe.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    """
    Turn on SQLite's foreign key enforcement for every new connection.

    This matters because SQLite has foreign key constraints OFF by
    default for backward-compatibility reasons — without this, deleting
    a Photo would silently leave orphaned Face rows behind instead of
    cascading, and the `ondelete="CASCADE"` / `ondelete="SET NULL"`
    settings declared on the models would be silently ignored.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# The session factory. autocommit=False and autoflush=False are the
# standard, predictable defaults: nothing is written to the DB until we
# explicitly call session.commit(), which keeps transaction boundaries
# obvious and easy to reason about.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session for a single
    request and guarantees it's closed afterward, even if the request
    raises an exception.

    Usage in a future router:
        def list_photos(db: Annotated[Session, Depends(get_db)]): ...

    The try/finally pattern here is important: without it, an exception
    raised inside a route would leak the session (and its underlying
    DB connection) instead of returning it to the pool.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
