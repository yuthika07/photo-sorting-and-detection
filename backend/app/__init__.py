"""
Wedding Photo Organizer — backend application package.

This package contains the entire FastAPI backend, organized using a
layered/clean-architecture style:

    api/       -> HTTP boundary (routers, dependency injection)
    core/      -> cross-cutting concerns (config, logging, exceptions)
    schemas/   -> Pydantic models shared across the API
    services/  -> business logic (Phase 2+)
    db/        -> persistence layer (Phase 2)
    ai/        -> computer vision pipeline (Phase 3)
"""
