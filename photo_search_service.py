"""
Photo search service.

This is the first module in app/services/ — the business-logic layer
routers call into, rather than talking to repositories directly. Its
job here is small but important: validate that the request makes
sense (do these person ids actually exist?) BEFORE running the more
expensive search query, and translate "doesn't exist" into the kind of
error the API layer knows how to turn into a proper HTTP response.
"""

from __future__ import annotations

import logging
from typing import Sequence

from app.core.exceptions import NotFoundError
from app.db.models.person import Person
from app.db.models.photo import Photo
from app.db.repositories import PersonRepository, PhotoRepository


class PhotoSearchService:
    """
    Orchestrates a "find photos containing these people" search.

    Depends on the two Phase 2 repositories, not on raw SQLAlchemy —
    same layering as every other part of this project: routers call
    services, services call repositories, repositories talk to the DB.
    """

    def __init__(
        self,
        person_repository: PersonRepository,
        photo_repository: PhotoRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Args:
            person_repository: used to validate the requested person ids.
            photo_repository: used to run the actual search query.
            logger: optional logger; defaults to "app.services.photo_search".
        """
        self._person_repository = person_repository
        self._photo_repository = photo_repository
        self._logger = logger or logging.getLogger("app.services.photo_search")

    def search_by_persons(self, person_ids: Sequence[int]) -> tuple[list[Person], list[Photo]]:
        """
        Find every photo containing ALL of the given people.

        Args:
            person_ids: one or more Person ids. "One" is a normal,
                valid case (search by a single person); more than one
                means AND semantics — every returned photo must contain
                every listed person, per this phase's requirement
                ("person 1 + person 2" means BOTH must appear).

        Returns:
            A tuple of (the matched Person rows, the matched Photo
            rows). Returning the resolved Person rows too — not just
            the ids the caller passed in — is what lets the API layer
            echo back each searched person's display_name in the
            response, so the client doesn't have to make a second
            request just to show "Searching for: Alice + Bob."

        Raises:
            NotFoundError: if ANY of the given person_ids doesn't exist.
                Validated up front, before the (more expensive) photo
                search runs — searching for a person who doesn't exist
                is a client mistake worth reporting clearly (404),
                not silently treating as "0 results."
        """
        unique_ids = sorted(set(person_ids))

        matched_persons = list(self._person_repository.list_by_ids(unique_ids))
        found_ids = {person.id for person in matched_persons}
        missing_ids = [pid for pid in unique_ids if pid not in found_ids]

        if missing_ids:
            raise NotFoundError(
                message=f"No person found for id(s): {missing_ids}",
                details={"missing_person_ids": missing_ids},
            )

        matched_photos = list(self._photo_repository.search_by_person_ids(unique_ids))

        self._logger.info(
            "Search by person_ids=%s matched %d photo(s)", unique_ids, len(matched_photos)
        )
        return matched_persons, matched_photos
