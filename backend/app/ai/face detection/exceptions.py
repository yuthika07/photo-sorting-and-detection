"""
Exceptions specific to the face detection module.

Same rationale as app/scanning/exceptions.py: this module has no HTTP
awareness, so it raises plain-Python exceptions. A future service layer
that calls into this module is responsible for catching these and
translating them into app/core/exceptions.py's AppException subclasses
at the API boundary.
"""


class FaceDetectionError(Exception):
    """Base class for all errors raised by the face detection module."""


class ModelLoadError(FaceDetectionError):
    """
    Raised when the SCRFD model file cannot be loaded — missing file,
    corrupted weights, or an incompatible ONNX Runtime environment.

    This is deliberately raised at SERVICE STARTUP (inside
    SCRFDFaceDetector.__init__), not on the first detection call — for
    an offline desktop app, "the bundled model is missing or broken" is
    exactly the kind of problem you want surfaced immediately and
    loudly, not silently on whatever random photo happens to be
    processed first.
    """


class InvalidImageError(FaceDetectionError):
    """
    Raised when an image file cannot be located or decoded — a missing
    path, a corrupted file, or a file that isn't actually a valid image
    despite its extension.
    """


class DetectionRuntimeError(FaceDetectionError):
    """
    Raised when the model loaded successfully, but inference on a
    specific image failed unexpectedly (e.g. an unusual image shape the
    model can't process). Kept distinct from ModelLoadError so callers
    can tell "the model itself is broken" apart from "this one image
    caused a problem" — the latter is recoverable by skipping the image
    and continuing a batch; the former is not.
    """
