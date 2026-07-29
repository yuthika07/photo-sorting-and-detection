"""
Database package.

Contents:
    base.py          -> declarative Base + TimestampMixin
    session.py        -> engine, SessionLocal, get_db() FastAPI dependency
    models/            -> ORM models: Photo, Face, Person
    repositories/        -> repository layer wrapping CRUD per model

Migrations are handled by Alembic, configured in backend/alembic.ini and
backend/migrations/ (kept at the backend root, alongside app/, rather
than nested inside app/, since Alembic is a standalone CLI tool that
operates on the project as a whole -- not application code that gets
imported at runtime).
"""
