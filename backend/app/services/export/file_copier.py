"""
Concrete file-copying implementation.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from app.services.export.interfaces import FileCopierBase


class SafeFileCopier(FileCopierBase):
    """
    Copies a file into a destination directory, preserving its original
    filename whenever possible, and safely renaming it if that exact
    filename is already taken in the destination.

    Uses shutil.copy2 rather than shutil.copy or shutil.move — see
    copy()'s docstring for why that specific choice matters.
    """

    def copy(self, source: Path, destination_dir: Path) -> Path:
        """
        Args:
            source: the original photo's path. Never modified or
                deleted — export is strictly additive, copying, never
                moving, so the user's original library is untouched no
                matter how many times they export.
            destination_dir: the folder to copy into.

        Returns:
            The path the file actually ended up at.
        """
        # Create the destination directory (and any missing parent
        # directories) if it doesn't exist yet. exist_ok=True means a
        # second photo copied into the same folder doesn't error out
        # trying to "recreate" a directory that's already there.
        destination_dir.mkdir(parents=True, exist_ok=True)

        target_path = destination_dir / source.name
        target_path = self._resolve_collision(target_path)

        # shutil.copy2 (as opposed to shutil.copy) also copies file
        # metadata -- specifically modification time and permission
        # bits -- alongside the file's contents. For a wedding photo
        # export, preserving the original modification timestamp
        # matters: many photo viewers and other tools sort by "date
        # modified", and a plain byte copy would reset it to "right
        # now," silently scrambling chronological order in the
        # exported folder.
        shutil.copy2(source, target_path)
        return target_path

    @staticmethod
    def _resolve_collision(target_path: Path) -> Path:
        """
        If `target_path` doesn't exist yet, use it as-is — this is the
        common case, and it's what "preserve original filenames" means
        by default.

        If it DOES exist already (two different source photos, from
        two different folders, happening to share a filename — a very
        real scenario with camera-generated names like "IMG_0001.jpg"
        from two different guests' phones), append a numeric suffix
        before the extension and try again, counting up until a free
        name is found. This never overwrites an existing file in the
        destination.
        """
        if not target_path.exists():
            return target_path

        stem = target_path.stem
        suffix = target_path.suffix
        counter = 1

        while True:
            candidate = target_path.with_name(f"{stem}_{counter}{suffix}")
            if not candidate.exists():
                return candidate
            counter += 1
