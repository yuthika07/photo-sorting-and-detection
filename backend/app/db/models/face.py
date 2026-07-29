"""
Face model — one row per detected face within a Photo.

A single Photo can contain many Faces (group shots). Each Face MAY be
linked to a Person once clustering/labeling has happened (Phase 3) —
`person_id` is nullable specifically so a freshly detected face can
exist before it's ever been assigned to anyone.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, Float, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.photo import Photo
    from app.db.models.person import Person


class Face(Base, TimestampMixin):
    """
    Represents one detected face: its location within a Photo, its
    embedding vector (for clustering), and which Person it belongs to,
    if known.
    """

    __tablename__ = "faces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Every Face MUST belong to exactly one Photo. ondelete="CASCADE"
    # means the DATABASE itself deletes this row if its Photo is
    # deleted — a safety net underneath the ORM-level cascade declared
    # on Photo.faces, so orphaned Face rows can't accumulate even if a
    # Photo is deleted by something other than the ORM.
    photo_id: Mapped[int] = mapped_column(
        ForeignKey("photos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Nullable: a face starts out unassigned. ondelete="SET NULL" means
    # deleting a Person un-links their faces rather than deleting the
    # face detections themselves — the face was still real, we just no
    # longer know (or have decided) who it belongs to.
    person_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Bounding box of the face within the photo, in pixel coordinates.
    # Stored as four plain integers rather than a packed string/JSON so
    # each value stays queryable and type-checked.
    bbox_x: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_y: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_width: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_height: Mapped[int] = mapped_column(Integer, nullable=False)

    # Raw embedding vector bytes (e.g. a 128- or 512-float array,
    # produced by Phase 3's face-embedding model). Stored as a BLOB —
    # see the repository layer notes on why NumPy (de)serialization
    # belongs in the service/AI layer, not here.
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    # Detector's confidence that this bounding box is really a face
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Many Faces -> one Photo
    photo: Mapped["Photo"] = relationship("Photo", back_populates="faces")

    # Many Faces -> one Person (optional). `foreign_keys` is spelled out
    # explicitly here even though there's only one FK to Person, as a
    # defensive habit — if a second FK to persons is ever added (there
    # isn't one today), SQLAlchemy would otherwise raise an ambiguous
    # relationship error instead of silently guessing wrong.
    person: Mapped["Person | None"] = relationship(
        "Person",
        back_populates="faces",
        foreign_keys=[person_id],
    )

    def __repr__(self) -> str:
        """Debug-friendly representation, e.g. in logs or a REPL."""
        return f"<Face id={self.id} photo_id={self.photo_id} person_id={self.person_id}>"
