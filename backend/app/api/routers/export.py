"""
Export router.

Same thin-router philosophy as search.py: parse the request, call the
service, shape the response. The one thing this router does that
search.py didn't need to is translate a module-specific exception
(InvalidDestinationError) into a core AppException — a concrete example
of the pattern described since Phase 4's docstrings ("a future service
layer is responsible for translating these at the API boundary").
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from app.api.deps import DBSessionDep
from app.core.exceptions import ValidationFailedError
from app.schemas.export import (
    ExportedFileSummary,
    ExportPhotosRequest,
    ExportPhotosResponse,
    SkippedFileSummary,
)
from app.services.export import InvalidDestinationError, create_default_photo_export_service

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/photos", response_model=ExportPhotosResponse)
def export_photos_by_persons(request: ExportPhotosRequest, db: DBSessionDep) -> ExportPhotosResponse:
    """
    Export every photo containing the given person(s) into a
    person-named subfolder under `destination_root`.

    Examples:
        {"person_ids": [1], "destination_root": "/Users/me/Desktop/export"}
            -> creates .../export/Alice/ and copies person 1's photos into it.
        {"person_ids": [1, 2], "destination_root": "/Users/me/Desktop/export"}
            -> creates .../export/Alice_Bob/ with only the photos where
               BOTH appear together.

    See this phase's written explanation for the full file-handling
    strategy (filename preservation, collision handling, per-file error
    isolation).
    """
    service = create_default_photo_export_service(db)
    destination_root = Path(request.destination_root)

    # InvalidDestinationError is this MODULE's own exception type (see
    # app/services/export/exceptions.py) — it has no HTTP meaning on
    # its own. This is exactly the translation boundary every prior AI
    # module's docstrings pointed to: catch it here, and re-raise as a
    # ValidationFailedError (a core AppException, 422) — the caller
    # supplied a bad path, which is a client input problem, not a
    # server bug.
    try:
        result = service.export_by_persons(request.person_ids, destination_root)
    except InvalidDestinationError as exc:
        raise ValidationFailedError(message=str(exc)) from exc

    # NotFoundError (unknown person_id, raised inside the reused Phase 7
    # search service) is a core AppException already — it propagates
    # uncaught here, same as in search.py, and Phase 1's global handler
    # converts it into a 404 automatically.

    return ExportPhotosResponse(
        output_folder=str(result.output_folder),
        exported_files=[
            ExportedFileSummary(source_path=str(f.source_path), destination_path=str(f.destination_path))
            for f in result.exported_files
        ],
        skipped_files=[
            SkippedFileSummary(source_path=str(f.source_path), reason=f.reason)
            for f in result.skipped_files
        ],
        total_exported=result.total_exported,
        total_skipped=result.total_skipped,
    )
