"""
Concrete face alignment implementation.
"""

from __future__ import annotations

import numpy as np
from insightface.utils import face_align

from app.ai.face_detection.models import FaceLandmarks
from app.ai.face_recognition.interfaces import FaceAlignerBase


class InsightFaceAligner(FaceAlignerBase):
    """
    Aligns a face crop using InsightFace's standard 5-point alignment:
    the same landmark convention (both eyes, nose, both mouth corners)
    produced by the face detection module's SCRFDFaceDetector.

    Why alignment matters at all: ArcFace was trained on faces that
    were rotated, scaled, and cropped into a consistent 112x112
    template — eyes always at roughly the same pixel positions, face
    always upright. A face crop taken directly from a bounding box (no
    alignment) might be tilted, off-center, or a different scale than
    what the model saw during training, which measurably hurts
    embedding quality. This class is what bridges Phase 4's raw
    landmarks into the exact input shape Phase 5's model expects.
    """

    def __init__(self, output_size: int = 112) -> None:
        """
        Args:
            output_size: the aligned crop's width/height in pixels.
                112 is ArcFace's standard trained input size — changing
                this without also changing the embedding model would
                produce a mismatched, degraded input.
        """
        self._output_size = output_size

    def align(self, image: np.ndarray, landmarks: FaceLandmarks) -> np.ndarray:
        """
        Args:
            image: the full BGR image the face was detected in.
            landmarks: the face's 5-point landmarks.

        Returns:
            A (output_size, output_size, 3) BGR aligned face crop.
        """
        # Convert our named, dataclass-based FaceLandmarks (from the
        # face_detection module) into the raw (5, 2) numpy array
        # insightface's alignment utility expects, in the SAME fixed
        # order it was produced in: left eye, right eye, nose, left
        # mouth corner, right mouth corner.
        keypoints = np.array(
            [
                [landmarks.left_eye.x, landmarks.left_eye.y],
                [landmarks.right_eye.x, landmarks.right_eye.y],
                [landmarks.nose.x, landmarks.nose.y],
                [landmarks.mouth_left.x, landmarks.mouth_left.y],
                [landmarks.mouth_right.x, landmarks.mouth_right.y],
            ],
            dtype=np.float32,
        )

        # norm_crop computes a similarity transform (rotation + scale +
        # translation) that maps these 5 points as close as possible to
        # ArcFace's fixed reference template, then warps the image
        # through that transform — this is what "alignment" means in
        # practice, not just cropping a rectangle.
        return face_align.norm_crop(image, landmark=keypoints, image_size=self._output_size)
