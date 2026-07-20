"""
Health check router.

Purpose: give the desktop shell (and developers) a fast, dependency-free
way to confirm the backend process is alive and responding before the
frontend webview tries to load or make real API calls.

This is intentionally the very first router in the project — it has no
dependency on the database or AI layers (which don't exist yet), so it
proves the FastAPI skeleton itself is wired up correctly end to end.
"""

from fastapi import APIRouter

from app.api.deps import SettingsDep
from app.schemas.common import HealthResponse

# prefix="" keeps this at the root, i.e. GET /health (not /health/health)
# tags=["health"] groups it under "health" in the auto-generated /docs UI
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health(settings: SettingsDep) -> HealthResponse:
    """
    Return basic liveness/version information about the running backend.

    Args:
        settings: injected application Settings (app name, version, env).

    Returns:
        A HealthResponse confirming the server is up, along with the
        app's name, version, and current environment — useful when a
        user reports a bug and you need to know which build they ran.
    """
    # Build and return the response model directly; FastAPI serializes
    # it to JSON automatically because of the response_model annotation
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )
