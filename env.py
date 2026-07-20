"""
Alembic environment script.

This is the ONE place migrations connect their two halves together:
"what should the schema look like" (our app's Settings + ORM models)
and "what does Alembic need to run a migration" (its Config/context
objects). Customized from Alembic's generated template in two ways:

  1. The database URL comes from app.core.config.get_settings()
     instead of a hardcoded value in alembic.ini — so migrations
     always target the same database the running app would use,
     controlled by the same .env file.
  2. target_metadata points at our models' Base.metadata, which is
     what enables `alembic revision --autogenerate` to detect model
     changes automatically.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Make the `app` package importable when Alembic is run as a standalone
# CLI from the backend/ directory (it doesn't go through uvicorn, so it
# doesn't automatically see our project's modules otherwise).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.db.models import Base  # noqa: E402  (imports Photo, Face, Person too)

# This is the Alembic Config object, giving access to values in alembic.ini
config = context.config

# Override whatever's in alembic.ini with our app's actual configured
# database URL, so there is exactly ONE source of truth (the .env file)
# instead of two (alembic.ini AND .env) that could drift out of sync.
config.set_main_option("sqlalchemy.url", get_settings().database_url)

# Set up Python logging as declared in alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point autogenerate at our real models' metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode: generate SQL without a live DB
    connection. Useful for producing a .sql script to hand to a DBA —
    not the normal path for this project, but kept for completeness
    since Alembic supports it out of the box.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode: connect to the real SQLite file
    and apply migrations directly. This is the path `alembic upgrade
    head` takes in normal development and deployment.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # render_as_batch=True is required for SQLite: SQLite's
            # ALTER TABLE support is very limited (e.g. it can't drop
            # or modify columns directly), so Alembic instead recreates
            # the table under the hood in "batch mode" to apply changes
            # that SQLite itself can't do with a plain ALTER TABLE.
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
