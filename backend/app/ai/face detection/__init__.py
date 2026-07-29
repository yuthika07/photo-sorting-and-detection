"""
Face detection module — locates faces within a photo using InsightFace's
SCRFD model, returning each face's bounding box, confidence score, and
5-point landmarks. Recognition (identifying WHO a face belongs to) is
explicitly out of scope for this phase — see scrfd_face_detector.py's
docstring for why the recognition model isn't even loaded.

Self-contained, same as app/scanning/: no dependency on the db/ or api/
layers. Takes an image (file path or array) in, returns DetectedFace
objects out. A future service will be responsible for turning each
DetectedFace into a Face row via FaceRepository.

Structure:

    exceptions.py                -> FaceDetectionError hierarchy
    models.py                     -> BoundingBox, Landmark, FaceLandmarks, DetectedFace
    interfaces.py                   -> abstract collaborator contracts (ABCs)
    image_loader.py                   -> OpenCVImageLoader
    scrfd_face_detector.py              -> SCRFDFaceDetector (loads the model once)
    face_detection_service.py             -> FaceDetectionService (the reusable service)

Quick start:

    from app.ai.face_detection import create_default_face_detection_service

    service = create_default_face_detection_service()
    faces = service.detect_in_file(Path("/path/to/photo.jpg"))
    for face in faces:
        print(face.confidence, face.bounding_box)
"""

from app.ai.face_detection.exceptions import (
    DetectionRuntimeError,
    FaceDetectionError,
    InvalidImageError,
    ModelLoadError,
)
from app.ai.face_detection.face_detection_service import FaceDetectionService
from app.ai.face_detection.image_loader import OpenCVImageLoader
from app.ai.face_detection.models import BoundingBox, DetectedFace, FaceLandmarks, Landmark
from app.ai.face_detection.scrfd_face_detector import SCRFDFaceDetector

from app.core.config import get_settings


def create_default_face_detection_service() -> FaceDetectionService:
    """
    Convenience factory that wires up a FaceDetectionService using this
    project's configured settings (model path, confidence threshold —
    see core/config.py's face_detection_* fields) and the default
    concrete implementations.

    This is what loads the SCRFD model — call it ONCE (e.g. at worker
    startup in a later phase) and reuse the returned service for every
    photo, rather than calling this factory per photo.
    """
    settings = get_settings()
    detector = SCRFDFaceDetector(
        model_path=settings.resolved_face_detection_model_path,
        confidence_threshold=settings.face_detection_confidence_threshold,
    )
    return FaceDetectionService(detector=detector, image_loader=OpenCVImageLoader())


__all__ = [
    "FaceDetectionService",
    "SCRFDFaceDetector",
    "OpenCVImageLoader",
    "BoundingBox",
    "Landmark",
    "FaceLandmarks",
    "DetectedFace",
    "FaceDetectionError",
    "ModelLoadError",
    "InvalidImageError",
    "DetectionRuntimeError",
    "create_default_face_detection_service",
]
