"""
Concrete duplicate-path detection implementation.
"""

from __future__ import annotations

from pathlib import Path

from app.scanning.interfaces import DuplicatePathDetectorBase


class InMemoryDuplicatePathDetector(DuplicatePathDetectorBase):
    """
    Tracks which paths have already been seen during a scan, using an
    in-memory set.

    Important design note on lifetime: an instance of this class holds
    state for exactly ONE scan's worth of history. Reusing the same
    instance across two separate calls to ImageScanner.scan() would
    cause every file in the second scan to be flagged as a duplicate of
    the first — so a fresh detector (or a fresh ImageScanner, which
    fresh-constructs its own) should be used per scan. This is called
    out explicitly here because it's the kind of subtle statefulness
    bug that's easy to introduce by accident when wiring dependencies.
    """

    def __init__(self) -> None:
        # Stores RESOLVED paths (see check_and_mark) so that two
        # different-looking paths pointing at the same real file (e.g.
        # via a symlink, or "./a.jpg" vs "a.jpg") are correctly treated
        # as the same path.
        self._seen_paths: set[Path] = set()

    def check_and_mark(self, path: Path) -> bool:
        """
        Resolve `path` to its canonical absolute form, check whether
        it's already been recorded, and record it either way.

        Args:
            path: the file path encountered during a scan.

        Returns:
            True if this path (after resolving symlinks/relative
            components) was already seen — i.e. it's a duplicate.
            False if this is the first time it's been encountered.
        """
        # Path.resolve() follows symlinks and collapses ".." / "."
        # segments, so "photos/a.jpg" and "photos/../photos/a.jpg"
        # correctly collide as the same path.
        resolved = path.resolve()

        if resolved in self._seen_paths:
            return True

        self._seen_paths.add(resolved)
        return False
