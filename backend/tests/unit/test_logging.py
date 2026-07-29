"""
Tests for app/core/logging.py (Phase 1).
"""

from __future__ import annotations

import logging

from app.core.config import Settings
from app.core.logging import configure_logging


class TestConfigureLogging:
    def test_creates_log_file_and_directory(self) -> None:
        settings = Settings()
        configure_logging(settings)

        assert settings.resolved_log_dir.exists()
        assert (settings.resolved_log_dir / "app.log").exists()

    def test_respects_configured_log_level(self) -> None:
        settings = Settings(log_level="WARNING")
        configure_logging(settings)

        assert logging.getLogger().level == logging.WARNING

    def test_reconfiguring_does_not_duplicate_handlers(self) -> None:
        settings = Settings()
        configure_logging(settings)
        configure_logging(settings)

        # console + file handler = 2, regardless of how many times this runs
        assert len(logging.getLogger().handlers) == 2
