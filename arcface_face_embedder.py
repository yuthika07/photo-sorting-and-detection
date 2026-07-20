"""
ArcFace face embedder implementation.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from insightface.model_zoo import ArcFaceONNX

from app.ai.face_detection.models import FaceLandmarks
from app.ai.face_recognition.exceptions import (
    EmbeddingExtractionError,
    InvalidLandmarksError,
    ModelLoadError,
)
from app.ai.face_recognition.interfaces import FaceAlignerBase, FaceEmbedderBase
from app.ai.face_recognition.models import FaceEmbedding


class ArcFaceEmbedder(FaceEmbedderBase):
    """
    Face embedder backed by InsightFace's ArcFace model, running
    locally via ONNX Runtime. Produces a 512-dimensional, L2-normalized
    vector per face — see this phase's explanation for what that vector
    represents and why it's normalized.

    Same "load once, reuse many times" design as SCRFDFaceDetector: the
    ONNX inference session is built once in __init__ and reused across
    every face embedded afterward.
    """

    #: ArcFace's standard output dimensionality. Declared as a class
    #: constant (not just a magic number scattered through the file) so
    #: it's checked against what the loaded model actually reports,
    #: and referenced consistently everywhere it's needed.
    EMBEDDING_DIMENSION = 512

    def __init__(
        self,
        model_path: Path,
        aligner: FaceAlignerBase,
        model_name: str = "arcface_w600k_mbf",
        use_gpu: bool = False,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Args:
            model_path: path to the bundled ArcFace .onnx weight file.
            aligner: aligns a raw image + landmarks into the model's
                expected input crop before embedding.
            model_name: a stable identifier stored on every produced
                FaceEmbedding, so embeddings can never be silently
                compared across different underlying models.
            use_gpu: same rationale as SCRFDFaceDetector — defaults to
                CPU (False) since this is a desktop app.
            logger: optional logger; defaults to "app.ai.face_recognition".

        Raises:
            ModelLoadError: if `model_path` doesn't exist, the model
                fails to load, or it doesn't actually produce
                EMBEDDING_DIMENSION-length vectors. All three are
                caught here, at construction time, not on first use.
        """
        self._aligner = aligner
        self._model_name = model_name
        self._logger = logger or logging.getLogger("app.ai.face_recognition")

        if not model_path.exists():
            raise ModelLoadError(
                f"ArcFace model file not found at {model_path}. "
                "The model must be bundled locally under backend/models/ "
                "— this app never downloads model weights at runtime."
            )

        try:
            self._model = ArcFaceONNX(model_file=str(model_path))
            ctx_id = 0 if use_gpu else -1
            self._model.prepare(ctx_id=ctx_id)
        except Exception as exc:
            raise ModelLoadError(f"Failed to load ArcFace model from {model_path}: {exc}") from exc

        # Fail fast if someone points this class at an incompatible
        # model file (right format, wrong architecture) — better to
        # catch a dimension mismatch here than to silently store
        # wrongly-shaped vectors that break every future comparison.
        reported_dimension = self._model.output_shape[-1]
        if reported_dimension != self.EMBEDDING_DIMENSION:
            raise ModelLoadError(
                f"Expected a {self.EMBEDDING_DIMENSION}-dimensional embedding model, "
                f"but {model_path} reports {reported_dimension} dimensions."
            )

        self._logger.info(
            "ArcFace model loaded once from %s (dimension=%d, device=%s)",
            model_path,
            self.EMBEDDING_DIMENSION,
            "GPU" if use_gpu else "CPU",
        )

    @property
    def model_name(self) -> str:
        """Stable identifier for this embedder's underlying model."""
        return self._model_name

    def generate_embedding(self, image: np.ndarray, landmarks: FaceLandmarks) -> FaceEmbedding:
        """
        Align the given face and generate its normalized embedding.

        Args:
            image: the full BGR image the face was detected in.
            landmarks: the face's 5-point landmarks (from the face
                detection module) — required for alignment.

        Returns:
            A 512-dimensional, L2-normalized FaceEmbedding.

        Raises:
            InvalidLandmarksError: if landmarks is None — ArcFace's
                accuracy depends on alignment, so this module refuses
                to embed an unaligned, arbitrary crop.
            EmbeddingExtractionError: if alignment or inference fails.
        """
        if landmarks is None:
            raise InvalidLandmarksError(
                "ArcFace requires 5-point facial landmarks for alignment; "
                "none were provided. Run face detection first and pass its "
                "landmarks through."
            )

        try:
            aligned_face = self._aligner.align(image, landmarks)
            raw_vector = self._model.get_feat(aligned_face).flatten()
        except (InvalidLandmarksError, EmbeddingExtractionError):
            raise
        except Exception as exc:
            raise EmbeddingExtractionError(f"Failed to generate embedding: {exc}") from exc

        normalized_vector = self._l2_normalize(raw_vector)

        return FaceEmbedding(
            vector=normalized_vector,
            dimension=self.EMBEDDING_DIMENSION,
            model_name=self._model_name,
        )

    @staticmethod
    def _l2_normalize(vector: np.ndarray) -> np.ndarray:
        """
        Scale `vector` to unit length (L2 norm of exactly 1.0).

        Raises:
            EmbeddingExtractionError: if the model produced a
                degenerate all-zero vector, which would make
                normalization divide by zero — this should never
                happen with a healthy model, but failing explicitly
                here is far better than silently propagating NaNs into
                every downstream similarity comparison.
        """
        norm = np.linalg.norm(vector)
        if norm == 0.0:
            raise EmbeddingExtractionError(
                "Model produced a degenerate zero-vector embedding; cannot normalize."
            )
        return (vector / norm).astype(np.float32)
