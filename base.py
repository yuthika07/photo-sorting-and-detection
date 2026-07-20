"""
Declarative base and shared mixins for ORM models.

Every model (Photo, Face, Person, and anything added later) inherits
from `Base`. Keeping this in its own tiny module — rather than defining
it inline in, say, photo.py — matters because Alembic and session.py
both need to import `Base.metadata` without pulling in a specific
model file, avoiding accidental circular imports.
"""

from datetime import datetime

# DeclarativeBase is SQLAlchemy 2.0's typed base class for ORM models
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# func.now() lets the DATABASE itself stamp timestamps (via SQL's
# CURRENT_TIMESTAMP) rather than relying on Python's clock, which keeps
# timestamps correct even if, e.g., a bulk import is scripted directly
# against the DB outside the normal app process
from sqlalchemy import DateTime, func


class Base(DeclarativeBase):
    """
    Base class every ORM model inherits from.

    `Base.metadata` is what Alembic reads to autogenerate migrations,
    and what session.py's `Base.metadata.create_all()` (used only for
    quick local testing, never in production — see session.py) reads to
    build tables directly.
    """

    pass


class TimestampMixin:
    """
    Adds `created_at` / `updated_at` columns to any model that mixes
    this in.

    Defined once here instead of copy-pasted into Photo, Face, and
    Person — if we ever need to change how timestamps behave (e.g.
    switch to timezone-aware datetimes), there's exactly one place to
    change it.
    """

    # server_default=func.now() means: if the application doesn't
    # supply a value, let SQLite set it at insert time
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # onupdate=func.now() means: every time a row is UPDATEd through
    # SQLAlchemy, this column is automatically refreshed — no service
    # code ever needs to remember to touch it manually
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
