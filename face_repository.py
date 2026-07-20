"""
Face repository — CRUD plus Face-specific lookups.
"""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.face import Face
from app.db.repositories.base_repository import BaseRepository


class FaceRepository(BaseRepository[Face]):
    """
    Repository for the Face model.
    """

    def __init__(self, db: Session) -> None:
        """Bind this repository to the Face model and the given session."""
        super().__init__(Face, db)

    def list_by_photo(self, photo_id: int) -> Sequence[Face]:
        """
        Fetch every detected face within a single photo.

        This is what the gallery/lightbox view will call to draw
        bounding boxes over a photo, and what a "tag this person"
        interaction operates on.
        """
        statement = select(Face).where(Face.photo_id == photo_id)
        return self.db.scalars(statement).all()

    def list_by_person(self, person_id: int, skip: int = 0, limit: int = 100) -> Sequence[Face]:
        """
        Fetch faces belonging to a specific, already-identified Person.

        Powers the "People" view: clicking a person shows every photo
        they appear in, driven by this query.
        """
        statement = (
            select(Face)
            .where(Face.person_id == person_id)
            .offset(skip)
            .limit(limit)
        )
        return self.db.scalars(statement).all()

    def list_unassigned(self, limit: int = 100) -> Sequence[Face]:
        """
        Fetch faces that have been detected but not yet linked to any
        Person.

        This is exactly the input set for the Phase 3 clustering stage:
        "take every unassigned face, group by embedding similarity, and
        propose Person clusters."
        """
        statement = select(Face).where(Face.person_id.is_(None)).limit(limit)
        return self.db.scalars(statement).all()

    def assign_to_person(self, face_id: int, person_id: int | None) -> Face | None:
        """
        Convenience wrapper to set (or clear, if person_id is None) a
        single face's person assignment.

        Kept as a named method rather than making every caller reach
        for the generic `update(db_obj, person_id=...)` — this is the
        single most common write this repository will see once face
        tagging is built, so it deserves an explicit, readable name.
        """
        face = self.get(face_id)
        if face is None:
            return None
        return self.update(face, person_id=person_id)
