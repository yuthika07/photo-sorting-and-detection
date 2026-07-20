"""
Application-wide logging configuration.

Why this exists as its own module: this is a desktop app running on a
user's machine — we can't SSH in and tail a server log when something
goes wrong. Every meaningful event needs to land in a rotating log file
on disk, in a consistent format, so a user's log folder can be zipped up
and inspected later to diagnose a bug report.
"""

# Standard library logging module — no extra dependency needed for this
import logging

# RotatingFileHandler caps log file size and keeps a few backups instead
# of letting one log file grow forever on a user's disk
from logging.handlers import RotatingFileHandler

# Used to make sure the log directory exists before we try to write to it
from pathlib import Path

from app.core.config import Settings


# Shared format string used by both console and file handlers, so log
# lines look identical everywhere: timestamp, level, module name, message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# Cap each log file at 5 MB and keep 5 rotated backups (25 MB max on disk)
MAX_LOG_FILE_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5


def configure_logging(settings: Settings) -> None:
    """
    Configure the root logger once, at application startup.

    Args:
        settings: the resolved application Settings, used to determine
            log level and log file location.

    This attaches two handlers to the root logger:
      1. A console handler (stdout) — useful during development.
      2. A rotating file handler — the durable record for diagnosing
         issues after the fact, since a desktop app has no remote
         observability tooling.
    """
    # Make sure the directory for log files actually exists on disk;
    # parents=True creates any missing intermediate directories, and
    # exist_ok=True avoids an error if it's already there.
    log_dir: Path = settings.resolved_log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    # Translate the LOG_LEVEL string ("INFO", "DEBUG", ...) into the
    # numeric constant the logging module actually uses internally
    numeric_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Grab the root logger — configuring this affects every logger created
    # anywhere in the app via logging.getLogger(__name__)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid attaching duplicate handlers if configure_logging() is ever
    # called more than once (e.g. in tests that spin up the app repeatedly)
    root_logger.handlers.clear()

    # Shared formatter instance used by both handlers below
    formatter = logging.Formatter(LOG_FORMAT)

    # --- Console handler: prints to stdout, visible during `uvicorn` dev runs
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # --- File handler: the durable, rotating record on disk
    file_handler = RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=MAX_LOG_FILE_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Log one line confirming setup succeeded — this is the first line
    # a developer (or future you) will see in app.log after launch
    root_logger.info(
        "Logging configured | level=%s | file=%s",
        settings.log_level,
        log_dir / "app.log",
    )
