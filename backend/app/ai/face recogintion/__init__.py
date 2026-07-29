"""
Face recognition module — generates a 512-dimensional, L2-normalized
identity embedding for a detected face using InsightFace's ArcFace
model. Clustering faces into Person groups is explicitly OUT of scope
for this phase — this module only produces and stores individual
embeddings; grouping them is a separate, later pipeline stage.

Self-contained in the same way as scanning/ and face_detection/, with
one deliberate exception: embedding_store.py DOES depend on the Phase 2
database layer (via FaceRepository), because "store embeddings" was an
explicit requirement of this phase and Face.embedding already exists
for exactly this purpose. Everything else here — the embedder, the
aligner, the serializer — has zero database awareness.

Structure:

    exceptions.py                 -> FaceRecognitionError hierarchy
    models.py                      -> FaceEmbedding (the reusable object)
    interfaces.py                    -> abstract collaborator contracts (ABCs)
    alignment.py                       -> InsightFaceAligner
    arcface_face_embedder.py             -> ArcFaceEmbedder (loads the model once)
    embedding_serializer.py                -> NumpyEmbeddingSerializer (vector <-> bytes)
    embedding_store.py                       -> SQLiteFaceEmbeddingStore (bytes <-> Face row)
    face_recognition_service.py                -> FaceRecognitionService (the reusable service)

Quick start (in-memory, no storage):

    from app.ai.face_detection import create_default_face_detection_service
    from app.ai.face_recognition import create_default_face_recognition_service

    detection_service = create_default_face_detection_service()
    recognition_service = create_default_face_recognition_service()

    image = ...  # a BGR numpy array, e.g. from OpenCVImageLoader
    faces = detection_service.detect_in_array(image)
    for face in faces:
        embedding = recognition_service.generate(image, face.landmarks)

Quick start (with storage, given a SQLAlchemy Session):

    service = create_default_face_recognition_service(db_session=session)
    service.generate_and_store(face_id=42, image=image, landmarks=face.landmarks)
"""

from sqlalchemy.orm import Session

from app.ai.face_recognition.alignment import InsightFaceAligner
from app.ai.face_recognition.arcface_face_embedder import ArcFaceEmbedder
from app.ai.face_recognition.embedding_serializer import NumpyEmbeddingSerializer
from app.ai.face_recognition.embedding_store import SQLiteFaceEmbeddingStore
from app.ai.face_recognition.exceptions import (
    EmbeddingExtractionError,
    FaceRecognitionError,
    InvalidLandmarksError,
    ModelLoadError,
)
from app.ai.face_recognition.face_recognition_service import FaceRecognitionService
from app.ai.face_recognition.models import FaceEmbedding
from app.core.config import get_settings
from app.db.repositories import FaceRepository

#: The model identifier stamped onto every embedding this module
#: produces via the default factory — kept in one place so the
#: embedder, the store, and any future comparison code all agree on it.
DEFAULT_MODEL_NAME = "arcface_w600k_mbf"


def create_default_face_recognition_service(
    db_session: Session | None = None,
) -> FaceRecognitionService:
    """
    Convenience factory wiring up a FaceRecognitionService from this
    project's configured settings and default concrete implementations.

    Args:
        db_session: an active SQLAlchemy session. If provided, the
            returned service is also wired with a SQLiteFaceEmbeddingStore,
            enabling generate_and_store()/load_stored(). If omitted, the
            service still works fully for generate()/to_bytes()/from_bytes()
            — it just can't persist anything, keeping this module usable
            with zero database setup when that's all a caller needs.

    This is what loads the ArcFace model — call it ONCE and reuse the
    returned service for every face, the same guidance as Phase 4's
    face detection factory.
    """
    settings = get_settings()
    aligner = InsightFaceAligner()
    embedder = ArcFaceEmbedder(
        model_path=settings.resolved_face_recognition_model_path,
        aligner=aligner,
        model_name=DEFAULT_MODEL_NAME,
    )
    serializer = NumpyEmbeddingSerializer()

    store: SQLiteFaceEmbeddingStore | None = None
    if db_session is not None:
        store = SQLiteFaceEmbeddingStore(
            face_repository=FaceRepository(db_session),
            serializer=serializer,
            model_name=DEFAULT_MODEL_NAME,
        )

    return FaceRecognitionService(embedder=embedder, serializer=serializer, store=store)


__all__ = [
    "FaceRecognitionService",
    "ArcFaceEmbedder",
    "InsightFaceAligner",
    "NumpyEmbeddingSerializer",
    "SQLiteFaceEmbeddingStore",
    "FaceEmbedding",
    "FaceRecognitionError",
    "ModelLoadError",
    "InvalidLandmarksError",
    "EmbeddingExtractionError",
    "create_default_face_recognition_service",
]
