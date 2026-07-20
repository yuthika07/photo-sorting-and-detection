"""
Photo model — one row per image file the user has imported.

This is the root entity of the whole schema: Faces belong to a Photo,
and (later, Phase 3+) Events/Albums reference Photos. Deliberately, this
table does NOT store the image bytes themselves — only `file_path`,
pointing at the original file on the user's disk — matching the
architecture decision to never duplicate a user's original wedding
photos into app-managed storage.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

# Only imported for type checkers, never at runtime — this avoids a
# circular import between photo.py and face.py while still giving you
# full autocomplete/type-checking on `photo.faces` in your editor.
if TYPE_CHECKING:
    from app.db.models.face import Face


class Photo(Base, TimestampMixin):
    """
    Represents a single imported photo and its file-level/EXIF metadata.

    AI-derived fields (file_hash, perceptual_hash, quality_score) are
    nullable because they're populated by later pipeline stages
    (Phase 3) — a freshly imported photo legitimately has all of them
    as NULL until processing catches up.
    """

    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Absolute path to the original file on the user's disk. Unique
    # because re-importing the same path should update, not duplicate,
    # the existing row (enforced in the repository/service layer).
    file_path: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)

    # SHA-256 of the file's bytes — used for EXACT duplicate detection
    file_hash: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    # Perceptual hash (pHash/dHash) — used for NEAR-duplicate / burst
    # detection; populated in the Phase 3 AI pipeline, not here
    perceptual_hash: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    # EXIF-derived capture timestamp — drives the timeline/event view
    taken_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    camera_model: Mapped[str | None] = mapped_column(String, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    orientation: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Composite blur/exposure score from Phase 3's quality-scoring stage
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Groups photos brought in together by one "Import" action, so an
    # import can be reviewed, retried, or undone as a unit
    import_batch_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    # One Photo -> many Faces. `cascade="all, delete-orphan"` means: if
    # a Photo row is deleted through the ORM, its Face rows are deleted
    # too — a Face can never meaningfully exist without its Photo.
    # `passive_deletes=True` lets the DB-level ON DELETE CASCADE (set on
    # Face.photo_id) do the actual deleting for bulk/SQL-level deletes,
    # while the ORM-level cascade covers deletes done through Python.
    faces: Mapped[list["Face"]] = relationship(
        "Face",
        back_populates="photo",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        """Debug-friendly representation, e.g. in logs or a REPL."""
        return f"<Photo id={self.id} file_path={self.file_path!r}>"
