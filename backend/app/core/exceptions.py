"""
Application exception hierarchy.

Every error that the API can return in a predictable, user-facing way
should be raised as one of these custom exception types rather than a
generic Exception. This lets us register ONE exception handler (in
main.py) that turns any of these into the same JSON error envelope, so
the frontend only ever has to parse one error shape:

    { "error": { "code": "...", "message": "...", "details": {...} } }

Domain-specific exceptions (e.g. CorruptImageError, ModelLoadError) will
be added in later phases by subclassing AppException — nothing about
this base class needs to change when that happens.
"""


class AppException(Exception):
    """
    Base class for all application-raised (as opposed to unexpected/bug)
    errors.

    Attributes:
        code: a short, machine-readable identifier (e.g. "NOT_FOUND").
            The frontend can switch on this to show tailored messages
            without parsing free-text strings.
        message: a human-readable explanation, safe to show in the UI.
        status_code: the HTTP status code this error should map to.
        details: optional extra structured context (e.g. which photo_id
            failed), merged into the JSON error response for debugging.
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: dict | None = None,
    ) -> None:
        """Store the error's fields and initialize the base Exception."""
        self.code = code
        self.message = message
        self.status_code = status_code
        # Default to an empty dict rather than None so callers can always
        # safely do `error.details.get(...)` without a None check
        self.details = details or {}
        # Pass message up to Exception so str(exc) still works normally
        super().__init__(message)


class NotFoundError(AppException):
    """
    Raised when a requested resource (photo, person, album, job, ...)
    does not exist. Maps to HTTP 404.
    """

    def __init__(self, message: str = "Resource not found", details: dict | None = None) -> None:
        super().__init__(code="NOT_FOUND", message=message, status_code=404, details=details)


class ValidationFailedError(AppException):
    """
    Raised when input passes basic type validation (Pydantic) but fails
    a business rule (e.g. an empty folder path, an unsupported file
    type). Maps to HTTP 422.
    """

    def __init__(self, message: str = "Validation failed", details: dict | None = None) -> None:
        super().__init__(code="VALIDATION_FAILED", message=message, status_code=422, details=details)


class ConfigurationError(AppException):
    """
    Raised when the application cannot start or operate correctly due to
    missing/invalid configuration (e.g. an unwritable data directory).
    Maps to HTTP 500, since this is a server-side setup problem, not
    something the end user did wrong.
    """

    def __init__(self, message: str = "Configuration error", details: dict | None = None) -> None:
        super().__init__(code="CONFIGURATION_ERROR", message=message, status_code=500, details=details)
