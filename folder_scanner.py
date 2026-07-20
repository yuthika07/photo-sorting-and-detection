"""
Concrete folder-walking implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from app.scanning.exceptions import InvalidScanRootError
from app.scanning.interfaces import FolderScannerBase


class RecursiveFolderScanner(FolderScannerBase):
    """
    Walks a directory tree recursively using pathlib, yielding every
    file it finds.

    Single Responsibility: this class does exactly one thing —
    traversal. It has no idea what a "supported image format" is and
    never will; that logic lives in ImageFormatValidatorBase
    implementations instead, so this class never needs to change if the
    list of supported formats changes.
    """

    def walk(self, root: Path) -> Iterator[Path]:
        """
        Yield every file under `root`, recursively, in the order
        pathlib's glob returns them (platform-dependent, not
        guaranteed sorted).

        Args:
            root: the folder to scan.

        Yields:
            Path objects for each file (directories themselves are
            never yielded — only their contents).

        Raises:
            InvalidScanRootError: if `root` doesn't exist or isn't a
                directory. Raised immediately, before any traversal
                happens, so a typo'd path fails fast and loudly rather
                than silently producing an empty result.
        """
        if not root.exists():
            raise InvalidScanRootError(f"Scan root does not exist: {root}")
        if not root.is_dir():
            raise InvalidScanRootError(f"Scan root is not a directory: {root}")

        # Path.rglob("*") recursively yields every entry (files AND
        # directories) under root; we filter to files only here, since
        # a directory entry is never something the rest of the pipeline
        # needs to see.
        for path in root.rglob("*"):
            if path.is_file():
                yield path
