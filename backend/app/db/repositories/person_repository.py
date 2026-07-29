"""
Person repository — CRUD plus Person-specific lookups.
"""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.person import Person
from app.db.repositories.base_repository import BaseRepository


class PersonRepository(BaseRepository[Person]):
    """
    Repository for the Person model.
    """

    def __init__(self, db: Session) -> None:
        """Bind this repository to the Person model and the given session."""
        super().__init__(Person, db)

    def list_confirmed(self, skip: int = 0, limit: int = 100) -> Sequence[Person]:
        """
        Fetch only persons the user has confirmed as correct.

        The "People" gallery view will default to showing confirmed
        persons first (or exclusively), since unconfirmed, auto-generated
        clusters are more likely to contain a clustering mistake.
        """
        statement = (
            select(Person)
            .where(Person.is_confirmed.is_(True))
            .offset(skip)
            .limit(limit)
        )
        return self.db.scalars(statement).all()

    def list_unconfirmed(self, skip: int = 0, limit: int = 100) -> Sequence[Person]:
        """
        Fetch auto-generated person clusters still awaiting user review.

        This is the queue a "Review suggested people" screen would page
        through after the Phase 3 clustering stage runs.
        """
        statement = (
            select(Person)
            .where(Person.is_confirmed.is_(False))
            .offset(skip)
            .limit(limit)
        )
        return self.db.scalars(statement).all()

    def get_by_display_name(self, display_name: str) -> Person | None:
        """
        Find a person by their exact display name.

        Useful when a user manually creates/labels a person and the
        app wants to check "does someone with this name already exist?"
        before creating a duplicate entry.
        """
        statement = select(Person).where(Person.display_name == display_name)
        return self.db.scalars(statement).first()

    def list_by_ids(self, person_ids: Sequence[int]) -> Sequence[Person]:
        """
        Fetch every Person row matching the given ids, in a single query.

        Used by the search API to validate that every id a caller asked
        to search by actually exists, before running the (more
        expensive) photo search — see PhotoSearchService for how a
        missing id turns into a 404 rather than a silently-empty result.
        """
        if not person_ids:
            return []
        statement = select(Person).where(Person.id.in_(set(person_ids)))
        return self.db.scalars(statement).all()
