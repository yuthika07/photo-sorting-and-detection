"""
ImageScanner — the orchestrator that composes every other class in this
module into one usable scan operation.
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.scanning.exceptions import ImageMetadataExtractionError
from app.scanning.interfaces import (
    DuplicatePathDetectorBase,
    FolderScannerBase,
    ImageFormatValidatorBase,
    MetadataExtractorBase,
)
from app.scanning.models import ScanReport


class ImageScanner:
    """
    Coordinates a folder scanner, format validator, duplicate detector,
    and metadata extractor to turn "a root folder" into a ScanReport.

    This class is intentionally the ONLY place in the module that knows
    about all four collaborators — everything else only knows its own
    narrow job (Single Responsibility). It depends on the abstract
    interfaces from interfaces.py, not on any concrete class (Dependency
    Inversion), which is what makes it possible to unit test this class
    with fake/mock collaborators, or to swap in a different metadata
    extractor later, without ever touching this file.
    """

    def __init__(
        self,
        folder_scanner: FolderScannerBase,
        format_validator: ImageFormatValidatorBase,
        duplicate_detector: DuplicatePathDetectorBase,
        metadata_extractor: MetadataExtractorBase,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Args:
            folder_scanner: walks the directory tree.
            format_validator: decides which files are supported images.
            duplicate_detector: tracks paths already processed in this scan.
            metadata_extractor: reads metadata for a validated image.
            logger: optional logger; defaults to "app.scanning" so log
                lines from this module are easy to filter in app.log.
        """
        self._folder_scanner = folder_scanner
        self._format_validator = format_validator
        self._duplicate_detector = duplicate_detector
        self._metadata_extractor = metadata_extractor
        self._logger = logger or logging.getLogger("app.scanning")

    def scan(self, root_folder: Path) -> ScanReport:
        """
        Scan `root_folder` recursively and return a full report.

        Args:
            root_folder: the folder to scan for images.

        Returns:
            A ScanReport containing every successfully read image's
            metadata, plus lists of duplicate, unsupported, and failed
            paths for transparency.

        Raises:
            InvalidScanRootError: propagated from the folder scanner if
                `root_folder` doesn't exist or isn't a directory — this
                is the one failure mode considered severe enough to
                abort the whole operation rather than being recorded in
                the report, since it means there's nothing to scan at all.
        """
        report = ScanReport(root_folder=root_folder)

        for path in self._folder_scanner.walk(root_folder):
            # Step 1: duplicate-path check runs FIRST, before format
            # validation or metadata extraction — no point doing more
            # expensive work on a path we're going to skip anyway.
            if self._duplicate_detector.check_and_mark(path):
                report.duplicate_paths.append(path)
                self._logger.debug("Skipping duplicate path: %s", path)
                continue

            # Step 2: ignore anything that isn't a supported image
            # format — silently, per this phase's requirement, though
            # we still record it in the report for transparency.
            if not self._format_validator.is_supported(path):
                report.unsupported_paths.append(path)
                continue

            # Step 3: attempt to read metadata. A single corrupted or
            # unreadable file must not abort the entire folder scan —
            # it's recorded and the scan continues, matching the
            # per-item error isolation strategy from the architecture doc.
            try:
                metadata = self._metadata_extractor.extract(path)
            except ImageMetadataExtractionError as exc:
                report.failed_paths.append((path, str(exc)))
                self._logger.warning("Failed to extract metadata: %s", exc)
                continue

            report.images.append(metadata)

        self._logger.info(
            "Scan complete for %s | images=%d duplicates=%d unsupported=%d failed=%d",
            root_folder,
            report.total_images_found,
            len(report.duplicate_paths),
            len(report.unsupported_paths),
            len(report.failed_paths),
        )
        return report
