"""
Abstract interfaces for the export service's collaborators.

Same SOLID pattern used throughout this project: PhotoExportService
depends on these abstractions, never directly on PersonFolderNamer or
SafeFileCopier — swapping the folder-naming policy or the copy strategy
later means writing a new class against one of these interfaces,
without touching the orchestrating service.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence

from app.db.models.person import Person


class FolderNamerBase(ABC):
    """Contract for turning a set of searched-for people into an output folder name."""

    @abstractmethod
    def build_folder_name(self, persons: Sequence[Person]) -> str:
        """
        Args:
            persons: the people this export was searched by (one or more).

        Returns:
            A filesystem-safe folder name, e.g. "Alice" for one person
            or "Alice_Bob" for two — see PersonFolderNamer for the
            exact naming/sanitization rules.
        """
        raise NotImplementedError


class FileCopierBase(ABC):
    """Contract for copying one file into a destination directory."""

    @abstractmethod
    def copy(self, source: Path, destination_dir: Path) -> Path:
        """
        Args:
            source: the original file's path.
            destination_dir: the folder to copy it into (created if
                it doesn't already exist).

        Returns:
            The actual path the file was written to — NOT guaranteed
            to be `destination_dir / source.name` if a filename
            collision required renaming; see SafeFileCopier.

        Raises:
            OSError: for any underlying filesystem failure (permission
                denied, disk full, etc). Deliberately left as the raw
                OSError rather than wrapped — PhotoExportService is the
                layer that decides whether a given failure should skip
                one file or abort the whole export.
        """
        raise NotImplementedError
