"""
Scanning module — recursively scans a folder for supported image files
and returns their metadata (width, height, filename, creation date),
skipping unsupported files and duplicate paths.

This module is deliberately self-contained: it has NO dependency on the
db/ layer, the api/ layer, or any HTTP framework. It takes a
pathlib.Path in, returns a ScanReport out. A future service (Phase 4)
will be the thing that calls ImageScanner and turns each ImageMetadata
into a Photo row via PhotoRepository — this module doesn't need to know
that will happen.

Structure (SOLID applied throughout — see individual file docstrings
for the reasoning behind each):

    exceptions.py             -> ScanningError hierarchy
    models.py                  -> ImageMetadata, ScanReport (plain dataclasses)
    interfaces.py                -> abstract collaborator contracts (ABCs)
    folder_scanner.py              -> RecursiveFolderScanner (pathlib-based)
    format_validator.py              -> ExtensionImageFormatValidator
    duplicate_path_detector.py         -> InMemoryDuplicatePathDetector
    metadata_extractor.py                -> PillowMetadataExtractor
    image_scanner.py                       -> ImageScanner (orchestrator)

Quick start:

    from pathlib import Path
    from app.scanning import create_default_image_scanner

    scanner = create_default_image_scanner()
    report = scanner.scan(Path("/path/to/wedding/photos"))
    print(report.total_images_found, "images found")
"""

from app.scanning.duplicate_path_detector import InMemoryDuplicatePathDetector
from app.scanning.exceptions import (
    ImageMetadataExtractionError,
    InvalidScanRootError,
    ScanningError,
)
from app.scanning.folder_scanner import RecursiveFolderScanner
from app.scanning.format_validator import ExtensionImageFormatValidator
from app.scanning.image_scanner import ImageScanner
from app.scanning.metadata_extractor import PillowMetadataExtractor
from app.scanning.models import ImageMetadata, ScanReport


def create_default_image_scanner() -> ImageScanner:
    """
    Convenience factory that wires up an ImageScanner using this
    module's default, concrete implementations.

    This exists purely for caller convenience — it does NOT weaken
    Dependency Inversion, since ImageScanner itself still only depends
    on the abstract interfaces. A caller with different needs (e.g. a
    test that wants a fake MetadataExtractor, or a future variant that
    supports more formats) can just construct ImageScanner directly
    with its own choice of collaborators instead of calling this.
    """
    return ImageScanner(
        folder_scanner=RecursiveFolderScanner(),
        format_validator=ExtensionImageFormatValidator(),
        duplicate_detector=InMemoryDuplicatePathDetector(),
        metadata_extractor=PillowMetadataExtractor(),
    )


__all__ = [
    "ImageScanner",
    "ImageMetadata",
    "ScanReport",
    "RecursiveFolderScanner",
    "ExtensionImageFormatValidator",
    "InMemoryDuplicatePathDetector",
    "PillowMetadataExtractor",
    "ScanningError",
    "InvalidScanRootError",
    "ImageMetadataExtractionError",
    "create_default_image_scanner",
]
