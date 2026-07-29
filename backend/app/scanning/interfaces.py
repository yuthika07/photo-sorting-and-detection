"""
Abstract interfaces for the scanning module's collaborators.

This file exists specifically to satisfy the Dependency Inversion
Principle: `ImageScanner` (the orchestrator in image_scanner.py) depends
on these abstractions, never on a concrete class like
`RecursiveFolderScanner` or `PillowMetadataExtractor` directly. Each
interface is also intentionally narrow (Interface Segregation) — a
class that only needs to validate formats doesn't have to implement
metadata extraction too.

Swapping an implementation later (e.g. reading dimensions with a
different library instead of Pillow, or walking folders with a
different traversal strategy) means writing a new class that satisfies
one of these interfaces — nothing in ImageScanner has to change
(Open/Closed Principle).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

from app.scanning.models import ImageMetadata


class FolderScannerBase(ABC):
    """
    Contract for anything that can walk a directory tree and yield file
    paths. Deliberately knows nothing about which files are images —
    that's the ImageFormatValidatorBase's job, not this one (Single
    Responsibility).
    """

    @abstractmethod
    def walk(self, root: Path) -> Iterator[Path]:
        """
        Yield every file path found under `root`, recursively.

        Args:
            root: the folder to scan.

        Yields:
            Path objects for each file encountered (not directories).
        """
        raise NotImplementedError


class ImageFormatValidatorBase(ABC):
    """
    Contract for deciding whether a given file path is a supported
    image format. Knows nothing about how to read metadata or walk
    folders — just "is this one of the types we handle?".
    """

    @abstractmethod
    def is_supported(self, path: Path) -> bool:
        """Return True if `path` should be treated as a supported image."""
        raise NotImplementedError


class MetadataExtractorBase(ABC):
    """
    Contract for reading metadata out of a single image file that has
    already been confirmed as a supported format.
    """

    @abstractmethod
    def extract(self, path: Path) -> ImageMetadata:
        """
        Read and return metadata for the image at `path`.

        Raises:
            ImageMetadataExtractionError: if the file cannot actually be
                read/decoded as an image (see exceptions.py).
        """
        raise NotImplementedError


class DuplicatePathDetectorBase(ABC):
    """
    Contract for tracking which file paths have already been seen
    during a scan, so the same path is never processed twice.
    """

    @abstractmethod
    def check_and_mark(self, path: Path) -> bool:
        """
        Check whether `path` has been seen before, and record it as
        seen regardless of the outcome.

        Returns:
            True if this path was already seen (i.e. it's a duplicate
            and should be skipped), False if this is the first time
            it's been encountered.
        """
        raise NotImplementedError
