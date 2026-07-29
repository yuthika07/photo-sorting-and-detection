"""
Abstract interfaces for the face recognition module's collaborators.

Same SOLID pattern as the scanning and face_detection modules: concrete
implementations (ArcFaceEmbedder, NumpyEmbeddingSerializer,
SQLiteFaceEmbeddingStore) are never referenced directly by the
orchestrating service — only through these abstractions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from app.ai.face_detection.models import FaceLandmarks
from app.ai.face_recognition.models import FaceEmbedding


class FaceAlignerBase(ABC):
    """
    Contract for turning a raw image + 5-point landmarks into a
    normalized, aligned face crop — the specific input shape and pose
    an embedding model expects.
    """

    @abstractmethod
    def align(self, image: np.ndarray, landmarks: FaceLandmarks) -> np.ndarray:
        """
        Args:
            image: the full BGR image the face was detected in.
            landmarks: the face's 5-point landmarks, as returned by the
                face detection module.

        Returns:
            A square, aligned face crop ready for the embedding model.
        """
        raise NotImplementedError


class FaceEmbedderBase(ABC):
    """
    Contract for turning an aligned (or alignable) face into a
    FaceEmbedding. Knows nothing about how embeddings get stored or
    compared — those are separate concerns (Single Responsibility).
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Stable identifier for the specific model producing embeddings."""
        raise NotImplementedError

    @abstractmethod
    def generate_embedding(self, image: np.ndarray, landmarks: FaceLandmarks) -> FaceEmbedding:
        """
        Args:
            image: the full BGR image the face was detected in.
            landmarks: the face's 5-point landmarks; required for alignment.

        Returns:
            A normalized FaceEmbedding.

        Raises:
            InvalidLandmarksError: if landmarks is None.
            EmbeddingExtractionError: if alignment or inference fails.
        """
        raise NotImplementedError


class EmbeddingSerializerBase(ABC):
    """Contract for converting a FaceEmbedding to/from raw bytes for storage."""

    @abstractmethod
    def to_bytes(self, embedding: FaceEmbedding) -> bytes:
        """Serialize an embedding for storage (e.g. in Face.embedding)."""
        raise NotImplementedError

    @abstractmethod
    def from_bytes(self, data: bytes, model_name: str) -> FaceEmbedding:
        """Reconstruct a FaceEmbedding from previously stored bytes."""
        raise NotImplementedError


class EmbeddingStoreBase(ABC):
    """
    Contract for persisting/retrieving an embedding associated with a
    specific Face record. Kept separate from EmbeddingSerializerBase:
    serialization is "vector <-> bytes"; storage is "bytes <-> a place
    they live," which for this project is the Face.embedding column
    from Phase 2 — but doesn't have to be.
    """

    @abstractmethod
    def save(self, face_id: int, embedding: FaceEmbedding) -> None:
        """Persist `embedding` against the Face row identified by `face_id`."""
        raise NotImplementedError

    @abstractmethod
    def load(self, face_id: int) -> FaceEmbedding | None:
        """
        Retrieve a previously stored embedding for `face_id`.

        Returns:
            The stored FaceEmbedding, or None if the Face doesn't exist
            or has no embedding stored yet.
        """
        raise NotImplementedError
