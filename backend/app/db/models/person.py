"""
Person model — represents one identity (a guest, a family member, ...)
that one or more Faces have been clustered or manually assigned to.

A Person can exist BEFORE it has a name: Phase 3's clustering stage
creates provisional Person rows from groups of visually similar faces,
and the user labels them later (`display_name` stays NULL until then,
`is_confirmed` stays False until a human confirms the cluster is
correct).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.face import Face


class Person(Base, TimestampMixin):
    """
    Represents one identity, backed by a cluster of Face rows.
    """

    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # NULL until the user (or a future auto-naming feature) labels this
    # person — e.g. "Aunt Carol"
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)

    # False for auto-generated clusters; True once a human has verified
    # the cluster actually represents one consistent person
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Deliberate design note: NOT a real foreign key -----------------
    # This is a "soft" reference to faces.id (the face used as this
    # person's thumbnail/cover image), stored as a plain Integer with NO
    # ForeignKey constraint. Why: Face already has a real FK to Person
    # (person_id). If Person also had a real FK to Face, the two tables
    # would depend on each other circularly, which SQLite's limited
    # ALTER TABLE support cannot express cleanly in a migration. Since
    # a "cover photo" pointer is a soft UX convenience — not a
    # relationship the data's integrity depends on — it's enforced in
    # the service layer (validate the id exists and belongs to this
    # person's faces) instead of the database layer. This trade-off is
    # documented here specifically so it isn't mistaken for an oversight.
    cover_face_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # One Person -> many Faces. No cascade delete here on purpose:
    # deleting a Person should NOT delete the underlying Face detections
    # (see Face.person_id's ondelete="SET NULL") — those faces are still
    # real data, they just become unassigned again.
    faces: Mapped[list["Face"]] = relationship(
        "Face",
        back_populates="person",
        foreign_keys="Face.person_id",
    )

    def __repr__(self) -> str:
        """Debug-friendly representation, e.g. in logs or a REPL."""
        return f"<Person id={self.id} display_name={self.display_name!r}>"
