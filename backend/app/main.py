"""
Application entry point.

This module exposes `app`, the FastAPI instance that uvicorn actually
runs. It is intentionally the ONLY file that wires everything together
(settings, logging, routers, exception handlers, startup/shutdown) — if
you ever need to see "how does this whole backend fit together?", this
file is the answer.

Run locally with:
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"""

# contextlib.asynccontextmanager lets us write FastAPI's modern "lifespan"
# startup/shutdown handler as a single async generator function
from contextlib import asynccontextmanager

# AsyncIterator is the correct type hint for an async generator's "yield"
from typing import AsyncIterator

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.exceptions import AppException
from app.api.routers import api_router

# Module-level logger for startup/shutdown/error events raised in this file
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Manage application startup and shutdown.

    Code before `yield` runs once, when the server starts (before it
    accepts any requests). Code after `yield` runs once, when the server
    is shutting down. This replaces FastAPI's older
    `@app.on_event("startup")` decorators with a single, easier-to-follow
    function.

    Args:
        app: the FastAPI application instance (unused directly here, but
            required by FastAPI's lifespan signature).
    """
    # --- STARTUP -----------------------------------------------------------
    settings = get_settings()

    # Logging must be configured before anything else logs a message
    configure_logging(settings)

    logger.info(
        "Starting %s v%s (env=%s) on %s:%s",
        settings.app_name,
        settings.app_version,
        settings.app_env,
        settings.host,
        settings.port,
    )

    # Ensure the data directory exists early, even though nothing writes
    # to it yet in Phase 1 — later phases (SQLite, thumbnails) assume it's
    # already there, and failing loudly now is better than failing deep
    # inside a future service call.
    settings.resolved_data_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Data directory ready at %s", settings.resolved_data_dir)

    # Hand control to the running application. Everything below this line
    # only executes once the server is shutting down.
    yield

    # --- SHUTDOWN ----------------------------------------------------------
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """
    Application factory.

    Building the app inside a function (instead of at module import time)
    makes testing much easier: a test suite can call `create_app()` to
    get a fresh instance, or override settings/dependencies, without any
    import-order side effects.

    Returns:
        A fully configured FastAPI instance, ready for uvicorn to serve.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        # Docs can be disabled entirely in production builds via env var
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url="/redoc" if settings.enable_docs else None,
        lifespan=lifespan,
    )

    # --- CORS --------------------------------------------------------------
    # Even though this is an offline app, the frontend (Next.js dev server
    # or the packaged desktop webview) is a different origin than the
    # backend, so CORS must be configured or the browser will block calls.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Exception handling --------------------------------------------------
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        """
        Convert any AppException (and its subclasses) raised anywhere in
        the app into the standard error envelope described in
        schemas/common.py, instead of FastAPI's default error shape.

        Args:
            request: the incoming request that triggered the error
                (unused directly, but required by FastAPI's handler
                signature; useful later for logging the request path).
            exc: the raised AppException instance.
        """
        logger.warning(
            "Handled application error: %s (%s) on %s %s",
            exc.code,
            exc.message,
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        """
        Catch-all for any error that ISN'T one of our AppException types
        — i.e. an actual bug. Logs the full stack trace (exc_info=True)
        so it's diagnosable from the log file, but returns a generic,
        safe message to the client rather than leaking internals.
        """
        logger.error(
            "Unhandled exception on %s %s",
            request.method,
            request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                    "details": {},
                }
            },
        )

    # --- Routing -------------------------------------------------------------
    # One line mounts every router aggregated in api/routers/__init__.py
    app.include_router(api_router)

    return app


# The actual ASGI application object uvicorn imports and serves.
app = create_app()
