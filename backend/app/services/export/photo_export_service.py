"""
PhotoExportService — the reusable, high-level entry point for exporting
photos by person.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Sequence

from app.services.export.exceptions import InvalidDestinationError
from app.services.export.interfaces import FileCopierBase, FolderNamerBase
from app.services.export.models import ExportedFile, ExportResult, SkippedFile
from app.services.photo_search_service import PhotoSearchService


class PhotoExportService:
    """
    Copies every photo matching a person search into a named output
    folder on disk.

    Deliberately built ON TOP OF PhotoSearchService (Phase 7) rather
    than duplicating any search logic — "export by person(s)" is just
    "search by person(s), then copy what was found." Reusing the exact
    same search also guarantees export results and search results can
    never silently disagree with each other.
    """

    def __init__(
        self,
        search_service: PhotoSearchService,
        folder_namer: FolderNamerBase,
        file_copier: FileCopierBase,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Args:
            search_service: finds the photos to export (Phase 7).
            folder_namer: decides the output subfolder's name.
            file_copier: performs the actual, safe file copy.
            logger: optional logger; defaults to "app.services.export".
        """
        self._search_service = search_service
        self._folder_namer = folder_namer
        self._file_copier = file_copier
        self._logger = logger or logging.getLogger("app.services.export")

    def export_by_persons(self, person_ids: Sequence[int], destination_root: Path) -> ExportResult:
        """
        Args:
            person_ids: one or more Person ids — same semantics as
                search: a single id exports that person's photos; more
                than one exports only the photos where ALL of them
                appear together.
            destination_root: an existing, writable directory. A
                person-named subfolder is created inside it — this
                method never writes directly into destination_root
                itself, so exporting several different person
                combinations into the same root never collides.

        Returns:
            An ExportResult listing every copied file and every file
            that had to be skipped, with a reason for each.

        Raises:
            NotFoundError: propagated from the search service if any
                person_id doesn't exist (see PhotoSearchService).
            InvalidDestinationError: if destination_root doesn't exist,
                isn't a directory, or isn't writable. Checked BEFORE
                the search even runs — no point finding 200 matching
                photos only to discover none of them can be written.
        """
        self._validate_destination(destination_root)

        # Reuses Phase 7 end to end: the same validation (unknown
        # person ids raise NotFoundError) and the same SQL search this
        # service's docstring is described relative to.
        persons, photos = self._search_service.search_by_persons(person_ids)

        folder_name = self._folder_namer.build_folder_name(persons)
        output_folder = destination_root / folder_name
        output_folder.mkdir(parents=True, exist_ok=True)

        result = ExportResult(output_folder=output_folder)

        for photo in photos:
            source_path = Path(photo.file_path)

            # Per-file isolation, same philosophy as every prior AI
            # module: a photo whose source file has since been moved,
            # renamed, or deleted on the user's disk (the database
            # doesn't know that happened until it tries) should not
            # abort exporting the other 199 photos that are still fine.
            if not source_path.exists():
                result.skipped_files.append(
                    SkippedFile(source_path=source_path, reason="Source file no longer exists on disk")
                )
                self._logger.warning("Skipping missing source file: %s", source_path)
                continue

            try:
                destination_path = self._file_copier.copy(source_path, output_folder)
            except OSError as exc:
                result.skipped_files.append(SkippedFile(source_path=source_path, reason=str(exc)))
                self._logger.warning("Skipping %s due to copy error: %s", source_path, exc)
                continue

            result.exported_files.append(
                ExportedFile(source_path=source_path, destination_path=destination_path)
            )

        self._logger.info(
            "Export complete: %d copied, %d skipped, output_folder=%s",
            result.total_exported,
            result.total_skipped,
            output_folder,
        )
        return result

    @staticmethod
    def _validate_destination(destination_root: Path) -> None:
        """
        Raises:
            InvalidDestinationError: if destination_root doesn't exist,
                isn't a directory, or this process can't write to it.
        """
        if not destination_root.exists():
            raise InvalidDestinationError(f"Destination folder does not exist: {destination_root}")
        if not destination_root.is_dir():
            raise InvalidDestinationError(f"Destination path is not a directory: {destination_root}")
        if not os.access(destination_root, os.W_OK):
            raise InvalidDestinationError(f"Destination folder is not writable: {destination_root}")
