"""
Common, cross-feature Pydantic schemas.

These are the shapes used by more than one router (health check, the
standard error envelope). Feature-specific schemas (photos, faces, ...)
will get their own files in later phases, e.g. schemas/photo.py.
"""

# BaseModel is the Pydantic class every schema inherits from
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """
    The inner "error" object of the standard error envelope.

    Every error response returned by this API — regardless of which
    endpoint raised it — will be shaped like:
        { "error": { "code": ..., "message": ..., "details": {...} } }
    """

    # Machine-readable error code, e.g. "NOT_FOUND" — stable, safe to
    # branch logic on in the frontend
    code: str = Field(..., description="Machine-readable error code")

    # Human-readable message, safe to display directly in the UI
    message: str = Field(..., description="Human-readable error message")

    # Optional extra structured context about the error (e.g. which
    # photo_id failed). Defaults to an empty dict, never null, so the
    # frontend doesn't need a None check before reading it.
    details: dict = Field(default_factory=dict, description="Optional extra context")


class ErrorResponse(BaseModel):
    """Top-level shape of every error response body returned by the API."""

    error: ErrorDetail


class HealthResponse(BaseModel):
    """
    Response shape for GET /health.

    The desktop shell polls this endpoint right after spawning the
    backend process, to know when it's safe to load the frontend
    webview — so this schema needs to stay simple and fast to produce.
    """

    status: str = Field(..., description="Overall health status, e.g. 'ok'")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current APP_ENV value")
