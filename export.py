"""
Schemas for the export API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExportPhotosRequest(BaseModel):
    """Request body for POST /export/photos."""

    person_ids: list[int] = Field(
        ...,
        min_length=1,
        description="One or more Person ids — same AND semantics as /search/photos",
    )
    destination_root: str = Field(
        ...,
        description=(
            "Absolute path to an existing, writable folder on disk. "
            "A person-named subfolder (e.g. 'Alice' or 'Alice_Bob') is "
            "created inside it; photos are copied there."
        ),
    )


class ExportedFileSummary(BaseModel):
    """One successfully copied file."""

    source_path: str
    destination_path: str


class SkippedFileSummary(BaseModel):
    """One file that could not be copied, and why."""

    source_path: str
    reason: str


class ExportPhotosResponse(BaseModel):
    """Response body for POST /export/photos."""

    output_folder: str
    exported_files: list[ExportedFileSummary]
    skipped_files: list[SkippedFileSummary]
    total_exported: int
    total_skipped: int
