"""
Shared fixtures for the entire test suite.

Design principle: every test gets a FRESH, isolated SQLite database —
either in-memory or a throwaway file, never the developer's real
data/app.db. This is what makes the suite safe to run repeatedly and
in parallel, and what makes each test's setup explicit rather than
depending on leftover state from a previous test.
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Face, Person, Photo  # noqa: F401  (registers models on Base.metadata)
from app.db.repositories import FaceRepository, PersonRepository, PhotoRepository
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """
    A fresh, isolated SQLite database for exactly one test.

    Uses `sqlite:///:memory:` with StaticPool so the same in-memory
    database is shared across every connection this engine hands out
    (SQLite's default behavior would otherwise give each connection
    its own separate, empty in-memory database, breaking anything that
    opens more than one connection). Tables are created directly from
    the ORM models' metadata — no Alembic involved — since tests want
    the fastest possible fresh schema, not a migration history.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def photo_repo(db_session: Session) -> PhotoRepository:
    return PhotoRepository(db_session)


@pytest.fixture()
def face_repo(db_session: Session) -> FaceRepository:
    return FaceRepository(db_session)


@pytest.fixture()
def person_repo(db_session: Session) -> PersonRepository:
    return PersonRepository(db_session)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    A FastAPI TestClient wired to the SAME isolated db_session as any
    repository fixtures used in the same test — this is what lets an
    API test seed data directly through a repository, then assert on
    what an HTTP call returns, without the two touching different
    databases.
    """

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def make_image(tmp_path: Path):
    """
    Factory fixture: make_image("a.jpg", size=(100, 100), color="red")
    writes a real, valid image file under tmp_path and returns its Path.

    Real image files (not just empty/fake bytes) matter here — the
    scanning module actually decodes them with Pillow, so a fixture
    that wrote garbage bytes would make every scanning test fail for
    the wrong reason.
    """

    def _make(
        filename: str,
        size: tuple[int, int] = (64, 64),
        color: str = "red",
        subdir: str | None = None,
    ) -> Path:
        directory = tmp_path / subdir if subdir else tmp_path
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / filename
        Image.new("RGB", size, color=color).save(path)
        return path

    return _make
