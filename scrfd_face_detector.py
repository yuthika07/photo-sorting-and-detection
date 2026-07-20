"""
SCRFD face detector implementation.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from insightface.model_zoo import SCRFD

from app.ai.face_detection.exceptions import DetectionRuntimeError, ModelLoadError
from app.ai.face_detection.interfaces import FaceDetectorBase
from app.ai.face_detection.models import BoundingBox, DetectedFace, FaceLandmarks, Landmark

# SCRFD's 5 keypoints are always returned in this fixed order — this is
# insightface's standard landmark convention, not something we choose.
_LANDMARK_FIELD_ORDER = ("left_eye", "right_eye", "nose", "mouth_left", "mouth_right")


class SCRFDFaceDetector(FaceDetectorBase):
    """
    Face detector backed by InsightFace's SCRFD (Sample and Computation
    Redistribution for efficient Face Detection) model, running locally
    via ONNX Runtime.

    The model is loaded exactly ONCE, in __init__ — never per-call. This
    matters a lot in practice: loading an ONNX model and building its
    inference session takes real time (parsing the graph, allocating
    buffers), while running inference on an already-loaded model is
    comparatively fast. A single SCRFDFaceDetector instance is meant to
    be constructed once (e.g. at application/worker startup) and reused
    for every photo in the library — see FaceDetectionService, which is
    the reusable wrapper meant to be shared across a whole import batch.
    """

    def __init__(
        self,
        model_path: Path,
        confidence_threshold: float = 0.5,
        input_size: tuple[int, int] = (640, 640),
        use_gpu: bool = False,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Args:
            model_path: path to the bundled SCRFD .onnx weight file.
            confidence_threshold: minimum score (0.0-1.0) for a
                detection to be kept; see the class-level note on why
                0.5 is a reasonable default, not an arbitrary one.
            input_size: the (width, height) SCRFD resizes each image to
                internally before detecting. 640x640 is SCRFD's standard
                trained input size — a reasonable balance of accuracy
                and speed on CPU for typical wedding photo resolutions.
            use_gpu: if True, run on the first available GPU (ctx_id=0)
                instead of CPU (ctx_id=-1). Defaults to False because
                this is a desktop app that must work on any user's
                machine, many without a compatible GPU/driver stack.
            logger: optional logger; defaults to "app.ai.face_detection".

        Raises:
            ModelLoadError: if `model_path` doesn't exist, or the ONNX
                model fails to load for any reason (corrupted weights,
                an incompatible ONNX Runtime build, etc). Raised here,
                at construction time, so a broken bundled model is
                discovered immediately at startup — not silently on
                whichever photo happens to be processed first.
        """
        self._confidence_threshold = confidence_threshold
        self._input_size = input_size
        self._logger = logger or logging.getLogger("app.ai.face_detection")

        if not model_path.exists():
            raise ModelLoadError(
                f"SCRFD model file not found at {model_path}. "
                "The model must be bundled locally under backend/models/ "
                "— this app never downloads model weights at runtime."
            )

        try:
            self._model = SCRFD(model_file=str(model_path))
            # ctx_id selects the compute device: -1 = CPU, 0+ = GPU index.
            # This is where the model's ONNX Runtime inference session is
            # actually built — the expensive, one-time setup work.
            ctx_id = 0 if use_gpu else -1
            self._model.prepare(ctx_id=ctx_id, input_size=self._input_size)
        except Exception as exc:
            # Any failure while constructing/preparing the model — file
            # is present but corrupted, incompatible ONNX opset, etc —
            # is wrapped in our own exception type so callers never need
            # to know insightface/onnxruntime's specific exception classes.
            raise ModelLoadError(f"Failed to load SCRFD model from {model_path}: {exc}") from exc

        self._logger.info(
            "SCRFD model loaded once from %s (input_size=%s, device=%s, threshold=%.2f)",
            model_path,
            self._input_size,
            "GPU" if use_gpu else "CPU",
            self._confidence_threshold,
        )

    def detect(self, image: np.ndarray) -> list[DetectedFace]:
        """
        Run face detection on an already-loaded image array.

        Args:
            image: a BGR numpy array (as produced by OpenCVImageLoader).

        Returns:
            A list of DetectedFace instances that met the configured
            confidence threshold, each with a bounding box, confidence
            score, and 5-point landmarks.

        Raises:
            DetectionRuntimeError: if the image array is empty/invalid,
                or if the underlying model raises during inference.
        """
        if image is None or image.size == 0:
            raise DetectionRuntimeError("Cannot run detection on an empty or invalid image array.")

        try:
            # SCRFD.detect returns two arrays:
            #   bboxes: shape (N, 5) -> [x1, y1, x2, y2, confidence_score]
            #   keypoints: shape (N, 5, 2) -> 5 (x, y) landmark points per face
            # N is however many raw candidate detections SCRFD found
            # BEFORE we apply our own confidence_threshold filter below.
            bboxes, keypoints = self._model.detect(
                image,
                input_size=self._input_size,
                max_num=0,  # 0 = no cap on the number of faces returned
                metric="default",
            )
        except Exception as exc:
            raise DetectionRuntimeError(f"SCRFD inference failed: {exc}") from exc

        detected_faces: list[DetectedFace] = []

        for index, bbox_row in enumerate(bboxes):
            x1, y1, x2, y2, score = bbox_row
            confidence = float(score)

            # Filter out low-confidence detections here, rather than in
            # the caller — the threshold is a property OF this detector
            # (it's configured at construction time), so enforcing it
            # here keeps that rule in exactly one place.
            if confidence < self._confidence_threshold:
                continue

            bounding_box = BoundingBox(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2))

            face_keypoints = keypoints[index] if keypoints is not None else None
            landmarks = self._build_landmarks(face_keypoints)

            detected_faces.append(
                DetectedFace(bounding_box=bounding_box, confidence=confidence, landmarks=landmarks)
            )

        return detected_faces

    @staticmethod
    def _build_landmarks(points: np.ndarray | None) -> FaceLandmarks | None:
        """
        Convert SCRFD's raw (5, 2) keypoint array into a named
        FaceLandmarks instance.

        Kept as a small static helper rather than inlined into detect()
        — translating "the model's raw array format" into "our stable,
        named data model" is a distinct piece of logic worth being able
        to read (and test) on its own.
        """
        if points is None:
            return None

        named_points = {
            field_name: Landmark(x=float(point_x), y=float(point_y))
            for field_name, (point_x, point_y) in zip(_LANDMARK_FIELD_ORDER, points)
        }
        return FaceLandmarks(**named_points)
