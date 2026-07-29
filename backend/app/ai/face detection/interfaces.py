"""
Abstract interfaces for the face detection module.

Same SOLID pattern used in app/scanning/interfaces.py: the reusable
service depends on these abstractions, never directly on
`SCRFDFaceDetector` or `OpenCVImageLoader`. This is what would let a
future Phase swap SCRFD for a different detector (or add a GPU-specific
variant) without changing FaceDetectionService at all.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np

from app.ai.face_detection.models import DetectedFace


class ImageLoaderBase(ABC):
    """Contract for loading an image file into an array the detector can use."""

    @abstractmethod
    def load(self, path: Path) -> np.ndarray:
        """
        Args:
            path: path to an image file on disk.

        Returns:
            The decoded image as a BGR numpy array (OpenCV's convention).

        Raises:
            InvalidImageError: if the file doesn't exist or can't be decoded.
        """
        raise NotImplementedError


class FaceDetectorBase(ABC):
    """
    Contract for anything that can find faces in an already-loaded
    image array. Knows nothing about file paths or how images get
    loaded — that's ImageLoaderBase's job (Single Responsibility).
    """

    @abstractmethod
    def detect(self, image: np.ndarray) -> list[DetectedFace]:
        """
        Args:
            image: a decoded image as a BGR numpy array.

        Returns:
            A list of DetectedFace instances, one per face found with
            confidence at or above the detector's configured threshold.
            An empty list is a valid, normal result (no faces found) —
            not an error.

        Raises:
            DetectionRuntimeError: if inference fails unexpectedly.
        """
        raise NotImplementedError
