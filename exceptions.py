"""
Exceptions specific to the export service.

Same rationale as the AI submodules' exceptions: no HTTP awareness
here. The router (app/api/routers/export.py) is responsible for
catching these and translating them into app/core/exceptions.py's
AppException subclasses at the API boundary — see that router for a
concrete example of the translation this module's docstrings have been
describing since Phase 4.
"""


class ExportError(Exception):
    """Base class for all errors raised by the export service."""


class InvalidDestinationError(ExportError):
    """
    Raised when the caller-supplied destination folder doesn't exist,
    isn't actually a directory, or isn't writable.

    Raised up front, before any file copying starts — a bad destination
    affects every single photo in the export, so this is exactly the
    kind of "environment-level" failure the architecture doc's error
    handling strategy says should abort the whole operation, unlike a
    single missing source photo (see PhotoExportService, which handles
    that per-file instead).
    """
