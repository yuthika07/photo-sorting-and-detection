"""
Generic base repository — standard CRUD operations shared by every
model-specific repository.

Why a repository layer exists at all: without it, CRUD-style SQLAlchemy
queries (`db.get(...)`, `db.execute(select(...))`, `db.add(...)`) end up
scattered across service functions and, eventually, copy-pasted between
them. The repository layer collects "how do I fetch/create/update/delete
a row" into one place per model, so:
  - services read like business logic, not SQL
  - swapping SQLite for another database later touches this layer only
  - each repository is easy to unit test against an in-memory DB
"""

from typing import Generic, TypeVar, Type, Sequence, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

# Bound to Base so type checkers know ModelType is always an ORM model
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic CRUD repository parameterized over a single ORM model type.

    Model-specific repositories (PhotoRepository, FaceRepository,
    PersonRepository) inherit from this and add query methods that are
    specific to that model (e.g. "find a photo by its file path").
    """

    def __init__(self, model: Type[ModelType], db: Session) -> None:
        """
        Args:
            model: the ORM model class this repository manages, e.g. Photo.
            db: an active SQLAlchemy Session, provided by the caller
                (typically injected via FastAPI's `Depends(get_db)` one
                layer up, in a service). The repository never creates
                its own session — that keeps transaction boundaries
                controlled by whoever is orchestrating the work.
        """
        self.model = model
        self.db = db

    def get(self, id_: int) -> ModelType | None:
        """
        Fetch a single row by primary key.

        Returns:
            The matching model instance, or None if no row has that id.
            Returning None (rather than raising) here is deliberate —
            "not found" is a normal, expected outcome for a repository
            method; the SERVICE layer decides whether that should
            become a 404 (raising NotFoundError from core/exceptions.py).
        """
        return self.db.get(self.model, id_)

    def list(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """
        Fetch a page of rows.

        Args:
            skip: how many rows to skip (for pagination).
            limit: maximum number of rows to return. Defaulted and
                always present so no caller can accidentally fetch an
                unbounded number of rows from a library of 10,000+ photos.
        """
        statement = select(self.model).offset(skip).limit(limit)
        return self.db.scalars(statement).all()

    def create(self, **fields: Any) -> ModelType:
        """
        Insert a new row.

        Args:
            **fields: column values for the new row, e.g.
                photo_repo.create(file_path="/photos/a.jpg").

        Returns:
            The newly created, fully persisted model instance (with its
            generated id and server-set timestamps populated, thanks to
            the refresh() call below).
        """
        obj = self.model(**fields)
        self.db.add(obj)
        self.db.commit()
        # Reload the object from the DB so server-generated values
        # (autoincrement id, server_default timestamps) are populated
        # on the Python object, not just written to the database
        self.db.refresh(obj)
        return obj

    def update(self, db_obj: ModelType, **fields: Any) -> ModelType:
        """
        Update an existing row in place.

        Args:
            db_obj: an already-fetched model instance (e.g. from get()).
            **fields: column values to overwrite.

        Returns:
            The same instance, refreshed with any server-computed values
            (e.g. the updated `updated_at` timestamp).
        """
        for field_name, value in fields.items():
            setattr(db_obj, field_name, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id_: int) -> bool:
        """
        Delete a row by primary key.

        Returns:
            True if a row was found and deleted, False if no row with
            that id existed. A bool return (rather than raising on
            "not found") keeps delete() idempotent and simple to call
            from cleanup code that doesn't care whether it already ran.
        """
        obj = self.get(id_)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
