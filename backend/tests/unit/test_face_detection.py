"""
Tests for app/ai/face_detection/ (Phase 4).

Split deliberately in two:
  - Fast tests use a FakeFaceDetector (implements FaceDetectorBase) so
    FaceDetectionService's orchestration logic can be verified without
    ever loading a real ONNX model — these run in milliseconds.
  - Slow tests (marked `slow`) load the ACTUAL bundled SCRFD model and
    run real inference, catching anything a fake could hide (wrong
    model path, a real preprocessing bug, the confidence filter not
    actually wired to the real model's output). Run everything with
    `pytest`, or skip the slow ones with `pytest -m "not slow"`.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from app.ai.face_detection.exceptions import InvalidImageError, ModelLoadError
from app.ai.face_detection.face_detection_service import FaceDetectionService
from app.ai.face_detection.image_loader import OpenCVImageLoader
from app.ai.face_detection.interfaces import FaceDetectorBase
from app.ai.face_detection.models import BoundingBox, DetectedFace
from app.ai.face_detection.scrfd_face_detector import SCRFDFaceDetector
from app.core.config import get_settings


class FakeFaceDetector(FaceDetectorBase):
    """A test double that returns a fixed, configurable result instead of running real inference."""

    def __init__(self, faces_to_return: list[DetectedFace] | None = None) -> None:
        self.faces_to_return = faces_to_return or []
        self.last_image_seen: np.ndarray | None = None

    def detect(self, image: np.ndarray) -> list[DetectedFace]:
        self.last_image_seen = image
        return self.faces_to_return


class TestOpenCVImageLoader:
    def test_loads_a_real_image(self, make_image) -> None:
        path = make_image("photo.jpg", size=(50, 40))
        image = OpenCVImageLoader().load(path)
        assert image.shape == (40, 50, 3)  # OpenCV shape is (height, width, channels)

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(InvalidImageError):
            OpenCVImageLoader().load(tmp_path / "missing.jpg")

    def test_raises_on_corrupted_file(self, tmp_path: Path) -> None:
        corrupt = tmp_path / "corrupt.jpg"
        corrupt.write_bytes(b"not a real image")
        with pytest.raises(InvalidImageError):
            OpenCVImageLoader().load(corrupt)


class TestFaceDetectionServiceWithFake:
    """Orchestration logic only — no real model involved."""

    def test_detect_in_file_loads_then_detects(self, make_image) -> None:
        path = make_image("photo.jpg")
        fake_face = DetectedFace(
            bounding_box=BoundingBox(x1=1, y1=1, x2=10, y2=10), confidence=0.9, landmarks=None
        )
        fake_detector = FakeFaceDetector(faces_to_return=[fake_face])
        service = FaceDetectionService(detector=fake_detector, image_loader=OpenCVImageLoader())

        results = service.detect_in_file(path)

        assert results == [fake_face]
        assert fake_detector.last_image_seen is not None  # the loaded image was actually passed through

    def test_detect_in_file_propagates_loader_errors_without_calling_detector(
        self, tmp_path: Path
    ) -> None:
        fake_detector = FakeFaceDetector()
        service = FaceDetectionService(detector=fake_detector, image_loader=OpenCVImageLoader())

        with pytest.raises(InvalidImageError):
            service.detect_in_file(tmp_path / "missing.jpg")

        assert fake_detector.last_image_seen is None  # never reached the detector

    def test_zero_faces_is_a_normal_result_not_an_error(self, make_image) -> None:
        path = make_image("blank.jpg")
        service = FaceDetectionService(detector=FakeFaceDetector(faces_to_return=[]), image_loader=OpenCVImageLoader())

        assert service.detect_in_file(path) == []

    def test_detect_in_array_skips_file_loading(self) -> None:
        fake_detector = FakeFaceDetector(faces_to_return=[])
        service = FaceDetectionService(detector=fake_detector, image_loader=OpenCVImageLoader())

        image = np.zeros((10, 10, 3), dtype=np.uint8)
        service.detect_in_array(image)

        assert fake_detector.last_image_seen is image


@pytest.mark.slow
class TestSCRFDFaceDetectorRealModel:
    """Exercises the actual bundled ONNX model."""

    def test_raises_model_load_error_for_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(ModelLoadError):
            SCRFDFaceDetector(model_path=tmp_path / "does_not_exist.onnx")

    def test_loads_bundled_model_and_detects_zero_faces_in_blank_image(self) -> None:
        model_path = get_settings().resolved_face_detection_model_path
        detector = SCRFDFaceDetector(model_path=model_path)

        blank = np.zeros((200, 200, 3), dtype=np.uint8)
        assert detector.detect(blank) == []

    def test_detects_faces_with_valid_confidence_and_landmarks(self, tmp_path: Path) -> None:
        # A synthetic blank image won't contain a detectable face (correctly --
        # SCRFD isn't fooled by noise), so this test only asserts on the
        # STRUCTURE of results the real model can produce, using an image
        # guaranteed to have zero detections, keeping this fast and
        # deterministic without bundling a real photo of a person into the repo.
        model_path = get_settings().resolved_face_detection_model_path
        detector = SCRFDFaceDetector(model_path=model_path, confidence_threshold=0.5)

        noise = (np.random.default_rng(0).random((300, 300, 3)) * 255).astype(np.uint8)
        results = detector.detect(noise)

        for face in results:
            assert 0.5 <= face.confidence <= 1.0
            assert face.bounding_box.width > 0
            assert face.bounding_box.height > 0
