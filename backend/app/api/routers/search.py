"""
Search router.

Exposes photo search by one or more people. Deliberately thin, per this
project's layering: this file only parses the request, calls
PhotoSearchService, and shapes the response — all real logic (id
validation, the actual query) lives one layer down.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import DBSessionDep
from app.db.repositories import PersonRepository, PhotoRepository
from app.schemas.search import PersonSummary, PhotoSummary, SearchPhotosResponse
from app.services.photo_search_service import PhotoSearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/photos", response_model=SearchPhotosResponse)
def search_photos_by_persons(
    db: DBSessionDep,
    person_ids: Annotated[
        list[int],
        Query(
            min_length=1,
            description=(
                "One or more Person ids. A single id searches by one "
                "person (e.g. ?person_ids=1). Multiple ids require ALL "
                "of them to appear together in a photo (e.g. "
                "?person_ids=1&person_ids=2 for 'person 1 + person 2')."
            ),
        ),
    ],
) -> SearchPhotosResponse:
    """
    Search for photos containing every one of the given people.

    Examples:
        GET /search/photos?person_ids=1
            -> every photo person 1 appears in.
        GET /search/photos?person_ids=1&person_ids=2
            -> only photos where BOTH person 1 AND person 2 appear.

    See this phase's written explanation for the full API flow (request
    -> validation -> SQL -> response) and the SQL query itself.
    """
    service = PhotoSearchService(
        person_repository=PersonRepository(db),
        photo_repository=PhotoRepository(db),
    )

    # NotFoundError (raised if any person_id doesn't exist) propagates
    # up uncaught — main.py's registered AppException handler (Phase 1)
    # converts it into a 404 with the standard error envelope. This
    # router never needs its own try/except for that; the exception
    # handling strategy set up in Phase 1 covers it automatically.
    matched_persons, matched_photos = service.search_by_persons(person_ids)

    return SearchPhotosResponse(
        persons=[
            PersonSummary(id=person.id, display_name=person.display_name)
            for person in matched_persons
        ],
        photos=[
            PhotoSummary(
                id=photo.id,
                file_path=photo.file_path,
                taken_at=photo.taken_at,
                width=photo.width,
                height=photo.height,
            )
            for photo in matched_photos
        ],
        total_photos=len(matched_photos),
    )
