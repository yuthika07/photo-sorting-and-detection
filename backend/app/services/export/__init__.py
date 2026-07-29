"""
Export service — copies photos matching a person search into a
person-named output folder on disk, preserving original filenames.

Structure:

    exceptions.py                -> ExportError hierarchy
    models.py                     -> ExportedFile, SkippedFile, ExportResult
    interfaces.py                   -> abstract collaborator contracts (ABCs)
    folder_namer.py                   -> PersonFolderNamer ("Alice", "Alice_Bob", ...)
    file_copier.py                      -> SafeFileCopier (preserves names, no overwrites)
    photo_export_service.py               -> PhotoExportService (built on Phase 7's search)

Quick start:

    from pathlib import Path
    from app.db.session import SessionLocal
    from app.services.export import create_default_photo_export_service

    db = SessionLocal()
    service = create_default_photo_export_service(db)
    result = service.export_by_persons([1, 2], Path("/Users/me/Desktop/wedding_export"))
    print(result.output_folder, result.total_exported, result.total_skipped)
"""

from sqlalchemy.orm import Session

from app.db.repositories import PersonRepository, PhotoRepository
from app.services.export.exceptions import ExportError, InvalidDestinationError
from app.services.export.file_copier import SafeFileCopier
from app.services.export.folder_namer import PersonFolderNamer
from app.services.export.models import ExportedFile, ExportResult, SkippedFile
from app.services.export.photo_export_service import PhotoExportService
from app.services.photo_search_service import PhotoSearchService


def create_default_photo_export_service(db_session: Session) -> PhotoExportService:
    """
    Convenience factory wiring up a PhotoExportService with the default
    concrete implementations and a Phase 7 PhotoSearchService bound to
    the given database session.
    """
    search_service = PhotoSearchService(
        person_repository=PersonRepository(db_session),
        photo_repository=PhotoRepository(db_session),
    )
    return PhotoExportService(
        search_service=search_service,
        folder_namer=PersonFolderNamer(),
        file_copier=SafeFileCopier(),
    )


__all__ = [
    "PhotoExportService",
    "PersonFolderNamer",
    "SafeFileCopier",
    "ExportedFile",
    "SkippedFile",
    "ExportResult",
    "ExportError",
    "InvalidDestinationError",
    "create_default_photo_export_service",
]
