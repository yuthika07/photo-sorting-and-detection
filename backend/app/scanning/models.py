"""
Data models returned by the scanning module.

These are plain dataclasses, not SQLAlchemy ORM models — this module is
intentionally decoupled from the database layer (see the package
docstring in __init__.py for why). A future service in Phase 4 will be
responsible for converting an ImageMetadata into a Photo row via
PhotoRepository.create(...).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ImageMetadata:
    """
    Metadata extracted from a single, successfully validated image file.

    frozen=True makes instances immutable — once metadata has been read
    for a file, nothing downstream should be able to accidentally mutate
    it (e.g. a bug that "fixes" a width in place, silently drifting from
    what's actually on disk).
    """

    file_path: Path
    filename: str
    width: int
    height: int
    created_at: datetime
    file_size_bytes: int


@dataclass
class ScanReport:
    """
    The full result of scanning one root folder: every image found,
    plus everything that was deliberately skipped and why.

    Returning a rich report — not just a bare list of images — matters
    for a wedding photo import: the user will want to know "412 photos
    found, 6 duplicates skipped, 2 unreadable files" rather than
    silently losing track of anything.
    """

    root_folder: Path
    images: list[ImageMetadata] = field(default_factory=list)
    duplicate_paths: list[Path] = field(default_factory=list)
    unsupported_paths: list[Path] = field(default_factory=list)
    # Each failure keeps the path AND a human-readable reason, so a
    # future UI can show the user exactly which files need attention
    failed_paths: list[tuple[Path, str]] = field(default_factory=list)

    @property
    def total_images_found(self) -> int:
        """Count of successfully validated and read images."""
        return len(self.images)

    @property
    def total_files_skipped(self) -> int:
        """Count of every file that did NOT become an ImageMetadata entry."""
        return len(self.duplicate_paths) + len(self.unsupported_paths) + len(self.failed_paths)
