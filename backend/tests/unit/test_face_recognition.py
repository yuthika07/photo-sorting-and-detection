"""
Tests for app/ai/face_recognition/ (Phase 5). Same fast/slow split
strategy as test_face_detection.py.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from app.ai.face_detection.models import FaceLandmarks, Landmark
from app.ai.face_recognition.alignment import InsightFaceAligner
from app.ai.face_recognition.arcface_face_embedder import ArcFaceEmbedder
from app.ai.face_recognition.embedding_serializer import NumpyEmbeddingSerializer
from app.ai.face_recognition.embedding_store import SQLiteFaceEmbeddingStore
from app.ai.face_recognition.exceptions import FaceRecognitionError, InvalidLandmarksError, ModelLoadError
from app.ai.face_recognition.face_recognition_service import FaceRecognitionService
from app.ai.face_recognition.interfaces import FaceEmbedderBase
from app.ai.face_recognition.models import FaceEmbedding
from app.core.config import get_settings
from app.db.repositories import FaceRepository, PhotoRepository


def make_embedding(dimension: int = 512, model_name: str = "test-model", seed: int = 0) -> FaceEmbedding:
    rng = np.random.default_rng(seed)
    raw = rng.normal(size=dimension).astype(np.float32)
    normalized = raw / np.linalg.norm(raw)
    return FaceEmbedding(vector=normalized, dimension=dimension, model_name=model_name)


FAKE_LANDMARKS = FaceLandmarks(
    left_eye=Landmark(x=10, y=10),
    right_eye=Landmark(x=20, y=10),
    nose=Landmark(x=15, y=15),
    mouth_left=Landmark(x=11, y=20),
    mouth_right=Landmark(x=19, y=20),
)


class FakeEmbedder(FaceEmbedderBase):
    def __init__(self, embedding_to_return: FaceEmbedding) -> None:
        self._embedding = embedding_to_return

    @property
    def model_name(self) -> str:
        return self._embedding.model_name

    def generate_embedding(self, image, landmarks) -> FaceEmbedding:  # noqa: ANN001
        if landmarks is None:
            raise InvalidLandmarksError("landmarks required")
        return self._embedding


class TestFaceEmbeddingModel:
    def test_valid_construction(self) -> None:
        embedding = make_embedding()
        assert embedding.dimension == 512

    def test_shape_mismatch_raises(self) -> None:
        with pytest.raises(ValueError):
            FaceEmbedding(vector=np.zeros(10, dtype=np.float32), dimension=512, model_name="m")

    def test_vector_is_immutable(self) -> None:
        embedding = make_embedding()
        with pytest.raises(ValueError):
            embedding.vector[0] = 999.0

    def test_cosine_similarity_of_identical_embedding_is_one(self) -> None:
        embedding = make_embedding()
        assert embedding.cosine_similarity(embedding) == pytest.approx(1.0, abs=1e-5)

    def test_cosine_similarity_different_vectors_less_than_one(self) -> None:
        a = make_embedding(seed=1)
        b = make_embedding(seed=2)
        assert a.cosine_similarity(b) < 0.99

    def test_cosine_similarity_raises_on_model_mismatch(self) -> None:
        a = make_embedding(model_name="model-a")
        b = make_embedding(model_name="model-b")
        with pytest.raises(ValueError):
            a.cosine_similarity(b)

    def test_cosine_similarity_raises_on_dimension_mismatch(self) -> None:
        a = make_embedding(dimension=512)
        b = make_embedding(dimension=256)
        with pytest.raises(ValueError):
            a.cosine_similarity(b)


class TestNumpyEmbeddingSerializer:
    def test_round_trip_preserves_values(self) -> None:
        original = make_embedding(seed=5)
        serializer = NumpyEmbeddingSerializer()

        data = serializer.to_bytes(original)
        restored = serializer.from_bytes(data, model_name=original.model_name)

        assert restored.dimension == original.dimension
        assert original.cosine_similarity(restored) == pytest.approx(1.0, abs=1e-5)

    def test_serialized_size_matches_float32_dimension(self) -> None:
        embedding = make_embedding(dimension=512)
        data = NumpyEmbeddingSerializer().to_bytes(embedding)
        assert len(data) == 512 * 4  # float32 = 4 bytes each


class TestSQLiteFaceEmbeddingStore:
    def test_save_then_load_round_trip(self, photo_repo: PhotoRepository, face_repo: FaceRepository) -> None:
        photo = photo_repo.create(file_path="/a.jpg")
        face = face_repo.create(photo_id=photo.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1)
        store = SQLiteFaceEmbeddingStore(
            face_repository=face_repo, serializer=NumpyEmbeddingSerializer(), model_name="test-model"
        )
        embedding = make_embedding(model_name="test-model")

        store.save(face.id, embedding)
        loaded = store.load(face.id)

        assert loaded is not None
        assert embedding.cosine_similarity(loaded) == pytest.approx(1.0, abs=1e-5)

    def test_load_returns_none_when_no_embedding_stored(
        self, photo_repo: PhotoRepository, face_repo: FaceRepository
    ) -> None:
        photo = photo_repo.create(file_path="/a.jpg")
        face = face_repo.create(photo_id=photo.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1)
        store = SQLiteFaceEmbeddingStore(
            face_repository=face_repo, serializer=NumpyEmbeddingSerializer(), model_name="test-model"
        )

        assert store.load(face.id) is None

    def test_save_to_nonexistent_face_raises(self, face_repo: FaceRepository) -> None:
        store = SQLiteFaceEmbeddingStore(
            face_repository=face_repo, serializer=NumpyEmbeddingSerializer(), model_name="test-model"
        )
        with pytest.raises(FaceRecognitionError):
            store.save(9999, make_embedding())


class TestFaceRecognitionServiceWithFake:
    def test_generate_delegates_to_embedder(self) -> None:
        expected = make_embedding()
        service = FaceRecognitionService(embedder=FakeEmbedder(expected), serializer=NumpyEmbeddingSerializer())

        result = service.generate(np.zeros((10, 10, 3)), FAKE_LANDMARKS)

        assert result is expected

    def test_generate_and_store_without_store_raises(self) -> None:
        service = FaceRecognitionService(
            embedder=FakeEmbedder(make_embedding()), serializer=NumpyEmbeddingSerializer(), store=None
        )
        with pytest.raises(FaceRecognitionError):
            service.generate_and_store(1, np.zeros((10, 10, 3)), FAKE_LANDMARKS)

    def test_to_bytes_from_bytes_round_trip_via_service(self) -> None:
        embedding = make_embedding(model_name="svc-model")
        service = FaceRecognitionService(embedder=FakeEmbedder(embedding), serializer=NumpyEmbeddingSerializer())

        data = service.to_bytes(embedding)
        restored = service.from_bytes(data)

        assert restored.model_name == "svc-model"
        assert embedding.cosine_similarity(restored) == pytest.approx(1.0, abs=1e-5)


@pytest.mark.slow
class TestArcFaceEmbedderRealModel:
    def test_raises_model_load_error_for_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(ModelLoadError):
            ArcFaceEmbedder(model_path=tmp_path / "missing.onnx", aligner=InsightFaceAligner())

    def test_produces_normalized_512d_embedding(self, make_image) -> None:
        model_path = get_settings().resolved_face_recognition_model_path
        embedder = ArcFaceEmbedder(model_path=model_path, aligner=InsightFaceAligner())

        image_path = make_image("face.jpg", size=(112, 112))
        import cv2

        image = cv2.imread(str(image_path))
        landmarks = FaceLandmarks(
            left_eye=Landmark(x=35, y=45),
            right_eye=Landmark(x=75, y=45),
            nose=Landmark(x=56, y=65),
            mouth_left=Landmark(x=40, y=85),
            mouth_right=Landmark(x=72, y=85),
        )

        embedding = embedder.generate_embedding(image, landmarks)

        assert embedding.dimension == 512
        assert float(np.linalg.norm(embedding.vector)) == pytest.approx(1.0, abs=1e-4)

    def test_raises_invalid_landmarks_error_when_none(self, make_image) -> None:
        model_path = get_settings().resolved_face_recognition_model_path
        embedder = ArcFaceEmbedder(model_path=model_path, aligner=InsightFaceAligner())

        import cv2

        image = cv2.imread(str(make_image("face.jpg")))
        with pytest.raises(InvalidLandmarksError):
            embedder.generate_embedding(image, None)
