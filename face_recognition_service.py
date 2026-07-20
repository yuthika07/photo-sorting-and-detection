"""
FaceRecognitionService — the reusable, high-level entry point for this
module.
"""

from __future__ import annotations

import logging

import numpy as np

from app.ai.face_detection.models import FaceLandmarks
from app.ai.face_recognition.exceptions import FaceRecognitionError
from app.ai.face_recognition.interfaces import (
    EmbeddingSerializerBase,
    EmbeddingStoreBase,
    FaceEmbedderBase,
)
from app.ai.face_recognition.models import FaceEmbedding


class FaceRecognitionService:
    """
    Combines a FaceEmbedderBase, an EmbeddingSerializerBase, and
    (optionally) an EmbeddingStoreBase into one simple, reusable
    service — the same "construct once, call many times" shape as
    FaceDetectionService from Phase 4.

    The store is optional by design: this service is just as useful for
    generating embeddings to compare in memory (e.g. "does this new
    photo's face match this already-known person?") without ever
    touching the database. Persistence is an add-on capability, not a
    requirement baked into every use of this service.
    """

    def __init__(
        self,
        embedder: FaceEmbedderBase,
        serializer: EmbeddingSerializerBase,
        store: EmbeddingStoreBase | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Args:
            embedder: generates embeddings from an image + landmarks.
            serializer: converts embeddings to/from raw bytes.
            store: optional persistence adapter; required only for
                generate_and_store() / load_stored().
            logger: optional logger; defaults to "app.ai.face_recognition".
        """
        self._embedder = embedder
        self._serializer = serializer
        self._store = store
        self._logger = logger or logging.getLogger("app.ai.face_recognition")

    def generate(self, image: np.ndarray, landmarks: FaceLandmarks) -> FaceEmbedding:
        """
        Generate a normalized embedding for one face, without storing it.

        Args:
            image: the full BGR image the face was detected in.
            landmarks: the face's 5-point landmarks from face detection.

        Returns:
            A 512-dimensional, L2-normalized FaceEmbedding.
        """
        embedding = self._embedder.generate_embedding(image, landmarks)
        self._logger.info(
            "Generated %d-d embedding (model=%s)", embedding.dimension, embedding.model_name
        )
        return embedding

    def generate_and_store(self, face_id: int, image: np.ndarray, landmarks: FaceLandmarks) -> FaceEmbedding:
        """
        Generate an embedding and persist it against an existing Face row.

        Args:
            face_id: the id of the Face row this embedding belongs to.
            image: the full BGR image the face was detected in.
            landmarks: the face's 5-point landmarks.

        Returns:
            The generated (and now stored) FaceEmbedding.

        Raises:
            FaceRecognitionError: if this service was constructed
                without a store — persistence was never configured, so
                failing clearly here beats silently doing nothing.
        """
        if self._store is None:
            raise FaceRecognitionError(
                "No embedding store configured on this service; construct "
                "it with a `store` to use generate_and_store()."
            )

        embedding = self.generate(image, landmarks)
        self._store.save(face_id, embedding)
        self._logger.info("Stored embedding for face_id=%d", face_id)
        return embedding

    def load_stored(self, face_id: int) -> FaceEmbedding | None:
        """
        Retrieve a previously stored embedding without regenerating it.

        Raises:
            FaceRecognitionError: if this service was constructed
                without a store.
        """
        if self._store is None:
            raise FaceRecognitionError(
                "No embedding store configured on this service; construct "
                "it with a `store` to use load_stored()."
            )
        return self._store.load(face_id)

    def to_bytes(self, embedding: FaceEmbedding) -> bytes:
        """Serialize an embedding to raw bytes, without storing it anywhere."""
        return self._serializer.to_bytes(embedding)

    def from_bytes(self, data: bytes) -> FaceEmbedding:
        """Reconstruct an embedding from raw bytes produced by this service's model."""
        return self._serializer.from_bytes(data, model_name=self._embedder.model_name)
