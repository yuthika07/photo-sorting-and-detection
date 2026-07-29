"""
Concrete image-format validation implementation.
"""

from __future__ import annotations

from pathlib import Path

from app.scanning.interfaces import ImageFormatValidatorBase

# Frozenset (immutable) of extensions this project currently supports,
# per this phase's explicit requirement: jpg, jpeg, png.
DEFAULT_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png"})


class ExtensionImageFormatValidator(ImageFormatValidatorBase):
    """
    Decides whether a file is a supported image based on its file
    extension.

    Open/Closed Principle in action: adding support for, say, ".heic"
    later does NOT require modifying this class or ImageScanner — it
    only requires constructing this validator with a different
    `supported_extensions` set (or, if extension-based checking is no
    longer enough, writing an entirely new ImageFormatValidatorBase
    implementation, e.g. one that reads a file's magic bytes instead).
    """

    def __init__(self, supported_extensions: frozenset[str] = DEFAULT_SUPPORTED_EXTENSIONS) -> None:
        """
        Args:
            supported_extensions: lowercase, dot-prefixed extensions to
                treat as supported images (e.g. {".jpg", ".png"}).
                Defaults to this phase's required jpg/jpeg/png set.
        """
        # Normalize to lowercase once at construction time, so
        # is_supported() never has to re-normalize on every call
        self._supported_extensions = {ext.lower() for ext in supported_extensions}

    def is_supported(self, path: Path) -> bool:
        """
        Return True if `path`'s extension is in the supported set.

        `path.suffix` includes the leading dot (e.g. ".JPG") and is
        lowercased before comparison, so matching is case-insensitive —
        real photo folders routinely mix ".jpg" and ".JPG".
        """
        return path.suffix.lower() in self._supported_extensions
