"""
Data models returned by the face detection module.

Plain, immutable dataclasses — no dependency on the database layer or
any specific ML library's own output types. This is what lets
FaceDetectorBase implementations vary (SCRFD today, potentially a
different detector later) while everything downstream keeps working
against the same stable shape.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BoundingBox:
    """
    A face's location within an image, as two corner points in pixel
    coordinates: (x1, y1) is the top-left corner, (x2, y2) is the
    bottom-right corner. Using two corners (rather than, say, x/y/width
    /height) matches what SCRFD returns natively, avoiding an unnecessary
    conversion — and corner coordinates are what you want anyway for
    drawing a box or cropping a region with most image libraries.
    """

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        """Box width in pixels, derived rather than stored redundantly."""
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        """Box height in pixels, derived rather than stored redundantly."""
        return self.y2 - self.y1


@dataclass(frozen=True)
class Landmark:
    """A single (x, y) keypoint in pixel coordinates."""

    x: float
    y: float


@dataclass(frozen=True)
class FaceLandmarks:
    """
    The 5 facial keypoints SCRFD locates for every detected face, in
    insightface's standard, fixed order: both eyes, the nose tip, and
    both corners of the mouth.

    These matter beyond just "extra detail" — a later face-recognition
    stage (explicitly NOT built in this phase) uses these 5 points to
    rotate/scale each face into a consistent, aligned orientation before
    computing its embedding, since recognition accuracy depends heavily
    on comparing faces from the same canonical pose.
    """

    left_eye: Landmark
    right_eye: Landmark
    nose: Landmark
    mouth_left: Landmark
    mouth_right: Landmark


@dataclass(frozen=True)
class DetectedFace:
    """
    One face detected in one image: where it is, how confident the
    model is that it's really a face, and its 5 keypoints.
    """

    bounding_box: BoundingBox
    confidence: float
    landmarks: FaceLandmarks | None
