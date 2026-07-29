"""
Routers package.

This __init__.py aggregates every individual router (health.py,
search.py, export.py today; more in later phases) into a single
`api_router` object, so main.py only has to do ONE `app.include_router()`
call instead of importing and registering every router file by hand.

Adding a new feature area in a later phase is then just:
    1. Create app/api/routers/<feature>.py with its own APIRouter
    2. Import it below and add `api_router.include_router(...)`
main.py never needs to change.
"""

from fastapi import APIRouter

from app.api.routers.export import router as export_router
from app.api.routers.health import router as health_router
from app.api.routers.search import router as search_router

# The single router object that main.py mounts onto the FastAPI app.
# Every feature router is included here with its own prefix/tags so URLs
# stay organized as the API grows, e.g. /health, /search/photos, /export/photos, ...
api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(search_router)
api_router.include_router(export_router)
