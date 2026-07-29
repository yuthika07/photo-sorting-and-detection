"""
Concrete image loading implementation, backed by OpenCV.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.ai.face_detection.exceptions import InvalidImageError
from app.ai.face_detection.interfaces import ImageLoaderBase


class OpenCVImageLoader(ImageLoaderBase):
    """
    Loads an image file into a BGR numpy array using OpenCV's
    `cv2.imread`, which is the array format SCRFD's preprocessing
    expects natively (no extra conversion needed before detection).
    """

    def load(self, path: Path) -> np.ndarray:
        """
        Args:
            path: path to an image file on disk.

        Returns:
            A BGR numpy array of shape (height, width, 3).

        Raises:
            InvalidImageError: if the path doesn't exist, or OpenCV
                can't decode it as an image (corrupted file, unsupported
                format, or a non-image file with a misleading extension).
        """
        if not path.exists():
            raise InvalidImageError(f"Image file does not exist: {path}")

        # cv2.imread returns None on failure rather than raising — this
        # is a classic OpenCV gotcha, so we explicitly check and convert
        # it into a real exception instead of letting `None` silently
        # flow into the detector and fail with a confusing error later.
        image = cv2.imread(str(path))
        if image is None:
            raise InvalidImageError(
                f"Could not decode image (corrupted file or unsupported format): {path}"
            )

        return image
