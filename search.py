"""
Schemas for the search API.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PersonSummary(BaseModel):
    """A brief, display-oriented view of a Person, used to echo back who was searched for."""

    id: int
    display_name: str | None = Field(None, description="Null if this person hasn't been named yet")


class PhotoSummary(BaseModel):
    """A brief, display-oriented view of a Photo, returned as a search result."""

    id: int
    file_path: str
    taken_at: datetime | None = Field(None, description="EXIF capture time, if known")
    width: int | None = None
    height: int | None = None


class SearchPhotosResponse(BaseModel):
    """
    Response shape for GET /search/photos.

    Includes the resolved `persons` alongside `photos` specifically so
    the client can render "Searching for: Alice + Bob" without a second
    round trip — see PhotoSearchService.search_by_persons for why the
    service returns both.
    """

    persons: list[PersonSummary] = Field(..., description="The people that were searched for")
    photos: list[PhotoSummary] = Field(..., description="Photos containing ALL of the above people")
    total_photos: int = Field(..., description="Convenience count; equals len(photos)")
