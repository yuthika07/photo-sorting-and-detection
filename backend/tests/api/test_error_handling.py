"""
Tests for main.py's catch-all exception handler (Phase 1): an
unexpected bug in a service must never crash the server or leak
internal details to the client — it should come back as a safe,
generic 500.
"""

from __future__ import annotations

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.services import photo_search_service


@pytest.fixture()
def client_that_does_not_reraise(db_session: Session) -> Generator[TestClient, None, None]:
    """
    A TestClient built with raise_server_exceptions=False.

    By default, TestClient re-raises any exception that escapes a
    route handler into the TEST itself (useful for debugging most
    tests) — but that bypasses main.py's registered exception
    handlers entirely, which is exactly the behavior this test needs
    to exercise. Real deployments (uvicorn) always go through the
    handler; this fixture makes the test match that reality.
    """

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app, raise_server_exceptions=False)
    finally:
        app.dependency_overrides.clear()


class TestUnhandledExceptionHandler:
    def test_unexpected_error_returns_generic_500_not_a_crash(
        self, client_that_does_not_reraise: TestClient, person_repo, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        alice = person_repo.create(display_name="Alice")

        def boom(self, person_ids):  # noqa: ANN001, ARG001
            raise RuntimeError("a real bug with a stack trace, e.g. a secret path or query")

        monkeypatch.setattr(photo_search_service.PhotoSearchService, "search_by_persons", boom)

        response = client_that_does_not_reraise.get("/search/photos", params={"person_ids": [alice.id]})

        assert response.status_code == 500
        body = response.json()
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
        # The real exception message must NOT leak to the client
        assert "a real bug" not in response.text
