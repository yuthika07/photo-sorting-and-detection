"""
Repositories package.

Aggregates every model-specific repository so callers (future services)
can do:

    from app.db.repositories import PhotoRepository, FaceRepository, PersonRepository

instead of importing from each individual file.
"""

from app.db.repositories.base_repository import BaseRepository
from app.db.repositories.photo_repository import PhotoRepository
from app.db.repositories.face_repository import FaceRepository
from app.db.repositories.person_repository import PersonRepository

__all__ = [
    "BaseRepository",
    "PhotoRepository",
    "FaceRepository",
    "PersonRepository",
]
