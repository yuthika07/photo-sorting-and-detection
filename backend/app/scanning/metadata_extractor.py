"""
Concrete metadata extraction implementation, backed by Pillow.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL import UnidentifiedImageError

from app.scanning.exceptions import ImageMetadataExtractionError
from app.scanning.interfaces import MetadataExtractorBase
from app.scanning.models import ImageMetadata


class PillowMetadataExtractor(MetadataExtractorBase):
    """
    Reads width, height, filename, and creation date for an image file
    using the Pillow library.

    Dependency Inversion in practice: ImageScanner only ever talks to
    the MetadataExtractorBase interface. If this project later swaps
    Pillow for another imaging library, only this one class changes —
    ImageScanner's code is untouched.
    """

    def extract(self, path: Path) -> ImageMetadata:
        """
        Args:
            path: an image file path, already confirmed as a supported
                format by an ImageFormatValidatorBase.

        Returns:
            An ImageMetadata instance with width, height, filename,
            creation date, and file size populated.

        Raises:
            ImageMetadataExtractionError: if the file's extension
                looked valid but its contents could not actually be
                decoded as an image (corrupted file, truncated
                download, a non-image file that was simply renamed).
        """
        try:
            # Image.open() is lazy — it reads just enough of the file
            # to determine its format and dimensions, not the whole
            # pixel buffer, so this stays fast even for large photos.
            # The `with` block ensures the underlying file handle is
            # closed as soon as we're done with it.
            with Image.open(path) as image:
                width, height = image.size
        except (UnidentifiedImageError, OSError) as exc:
            # UnidentifiedImageError: Pillow recognized the file but
            # couldn't decode it as any known image format.
            # OSError: broader I/O failure (truncated file, permission
            # issue reading the file's contents, etc).
            # Both are wrapped in our own exception type so callers of
            # this module only ever need to catch ONE exception type,
            # never Pillow-specific ones.
            raise ImageMetadataExtractionError(
                f"Could not read image metadata for {path}: {exc}"
            ) from exc

        # NOTE on "creation date": this uses filesystem metadata
        # (st_ctime), NOT the photo's EXIF "DateTimeOriginal" (the
        # moment the camera shutter fired). On Linux, st_ctime is the
        # inode's last metadata-change time, not true creation time; on
        # Windows and macOS it more closely reflects actual file
        # creation. True EXIF-based capture time belongs to a later,
        # separate metadata-extraction stage (see the architecture
        # doc's AI Pipeline, stage 2) — this module intentionally only
        # covers what was asked of it here: filesystem-level creation
        # date.
        file_stats = path.stat()
        created_at = datetime.fromtimestamp(file_stats.st_ctime)

        return ImageMetadata(
            file_path=path,
            filename=path.name,
            width=width,
            height=height,
            created_at=created_at,
            file_size_bytes=file_stats.st_size,
        )
