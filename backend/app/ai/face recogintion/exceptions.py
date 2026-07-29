"""
Exceptions specific to the face recognition module.

Same rationale as the detection and scanning modules' exceptions: no
HTTP awareness here — a future service layer translates these into
app/core/exceptions.py's AppException subclasses at the API boundary.
"""


class FaceRecognitionError(Exception):
    """Base class for all errors raised by the face recognition module."""


class ModelLoadError(FaceRecognitionError):
    """
    Raised when the ArcFace model file cannot be loaded, or loads but
    doesn't produce the expected embedding dimension. Raised at
    construction time (inside ArcFaceEmbedder.__init__), same reasoning
    as the detection module: a broken bundled model should fail loudly
    at startup, not silently on whichever face is processed first.
    """


class InvalidLandmarksError(FaceRecognitionError):
    """
    Raised when embedding generation is attempted without the 5-point
    landmarks ArcFace's alignment step requires. This is what enforces,
    at the type level, that recognition always runs on an ALIGNED face
    — never a raw, arbitrarily-rotated crop — since alignment quality
    directly affects embedding quality.
    """


class EmbeddingExtractionError(FaceRecognitionError):
    """
    Raised when alignment or inference fails for a specific face — a
    degenerate crop, an unexpected image shape, or an internal model
    failure. Distinct from ModelLoadError for the same reason as the
    detection module's DetectionRuntimeError: "this one face failed" is
    recoverable (skip it, keep going); "the model itself is broken" is not.
    """
