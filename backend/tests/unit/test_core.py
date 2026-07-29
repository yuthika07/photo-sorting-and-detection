"""
Tests for app/core/ (Phase 1).
"""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.exceptions import AppException, NotFoundError, ValidationFailedError


class TestSettings:
    def test_defaults_are_sane(self) -> None:
        settings = Settings()
        assert settings.port > 0
        assert settings.app_env in {"development", "production", "test"}

    def test_get_settings_is_cached_singleton(self) -> None:
        assert get_settings() is get_settings()

    def test_cors_origins_list_splits_and_strips(self) -> None:
        settings = Settings(cors_origins="http://a.com, http://b.com ,http://c.com")
        assert settings.cors_origins_list == ["http://a.com", "http://b.com", "http://c.com"]

    def test_database_url_points_at_sqlite_file_in_data_dir(self) -> None:
        settings = Settings()
        assert settings.database_url.startswith("sqlite:///")
        assert settings.database_url.endswith("app.db")


class TestExceptionHierarchy:
    def test_not_found_error_defaults(self) -> None:
        error = NotFoundError()
        assert error.status_code == 404
        assert error.code == "NOT_FOUND"
        assert isinstance(error, AppException)

    def test_validation_failed_error_defaults(self) -> None:
        error = ValidationFailedError()
        assert error.status_code == 422
        assert error.code == "VALIDATION_FAILED"

    def test_details_default_to_empty_dict_not_none(self) -> None:
        error = NotFoundError()
        assert error.details == {}

    def test_custom_message_and_details_preserved(self) -> None:
        error = NotFoundError(message="custom message", details={"id": 42})
        assert str(error) == "custom message"
        assert error.details == {"id": 42}
