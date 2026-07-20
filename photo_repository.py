"""
Photo repository — CRUD plus Photo-specific lookups.
"""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.face import Face
from app.db.models.photo import Photo
from app.db.repositories.base_repository import BaseRepository


class PhotoRepository(BaseRepository[Photo]):
    """
    Repository for the Photo model.

    Inherits get/list/create/update/delete from BaseRepository and adds
    the handful of lookups that show up repeatedly once real features
    (import, dedup) are built in later phases.
    """

    def __init__(self, db: Session) -> None:
        """Bind this repository to the Photo model and the given session."""
        super().__init__(Photo, db)

    def get_by_file_path(self, file_path: str) -> Photo | None:
        """
        Find a photo by its exact original file path.

        This is the core lookup an import routine needs: before
        inserting a new Photo row, check whether this exact path was
        already imported, so re-running an import updates the existing
        row instead of creating a duplicate (file_path is also DB-level
        unique, so this doubles as a pre-check before hitting that
        constraint).
        """
        statement = select(Photo).where(Photo.file_path == file_path)
        return self.db.scalars(statement).first()

    def get_by_file_hash(self, file_hash: str) -> Sequence[Photo]:
        """
        Find all photos sharing an exact SHA-256 file hash.

        Used by the (Phase 3) duplicate-detection stage: an identical
        hash means byte-for-byte identical files, e.g. the same photo
        copied from two guests' phones into the same import folder.
        """
        statement = select(Photo).where(Photo.file_hash == file_hash)
        return self.db.scalars(statement).all()

    def list_by_import_batch(self, import_batch_id: str) -> Sequence[Photo]:
        """
        Fetch every photo brought in by one specific import run.

        Useful for showing "here's what was just imported" or for
        implementing an "undo this import" action.
        """
        statement = select(Photo).where(Photo.import_batch_id == import_batch_id)
        return self.db.scalars(statement).all()

    def list_unprocessed(self, limit: int = 100) -> Sequence[Photo]:
        """
        Fetch photos that haven't had AI processing run on them yet.

        A photo is considered unprocessed if it has no file_hash — the
        very first pipeline stage (Section 6 of the architecture doc).
        This is what the Phase 3 worker will query to know what's left
        to do, and what makes resuming an interrupted import possible.
        """
        statement = select(Photo).where(Photo.file_hash.is_(None)).limit(limit)
        return self.db.scalars(statement).all()

    def search_by_person_ids(self, person_ids: Sequence[int]) -> Sequence[Photo]:
        """
        Find every photo that contains ALL of the given people —
        i.e. "person 1" alone, or "person 1 AND person 2" together, per
        however many ids are passed in.

        Args:
            person_ids: one or more Person ids. Every returned photo
                contains at least one Face belonging to EACH id in this
                list — not just any one of them.

        Returns:
            Every matching Photo, ordered by capture time (oldest
            first) so results read like a timeline.

        Why this needs a JOIN, and why GROUP BY / HAVING (not just a
        WHERE filter), is explained in full in this phase's written
        explanation — the short version: Photo and Person have no
        direct relationship to each other; Face is the only table that
        connects them, so finding "photos containing person X" requires
        joining through Face. And because one Face row only ever
        references ONE person_id, matching "ALL of these people" means
        counting how many of the requested people were found per photo
        and requiring that count to equal the number requested.
        """
        # De-duplicate defensively — if a caller accidentally passes the
        # same person_id twice, the required "match count" below must
        # still be based on the number of DISTINCT people asked for.
        unique_person_ids = list(set(person_ids))
        required_match_count = len(unique_person_ids)

        statement = (
            select(Photo)
            # JOIN photos to faces on the foreign key linking them —
            # this is what lets a query about Photo rows filter based
            # on facts recorded in the Face table (see the written
            # explanation for why this relationship can't be expressed
            # any other way).
            .join(Face, Face.photo_id == Photo.id)
            # Narrow down to only the faces that belong to one of the
            # people we're searching for.
            .where(Face.person_id.in_(unique_person_ids))
            # Collapse the (possibly many) matching Face rows per photo
            # down to one group per photo, so we can count how many
            # DISTINCT requested people were found in each photo.
            .group_by(Photo.id)
            # Keep only photos where EVERY requested person was found —
            # not just some of them. This is what turns "photos with
            # ANY of these people" into "photos with ALL of these people."
            .having(func.count(func.distinct(Face.person_id)) == required_match_count)
            .order_by(Photo.taken_at)
        )
        return self.db.scalars(statement).all()
