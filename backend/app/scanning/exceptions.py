"""
Exceptions specific to the scanning module.

Kept separate from app/core/exceptions.py deliberately: those are HTTP-
facing AppException types meant to be caught by main.py's exception
handlers and turned into API responses. This module has no HTTP
awareness at all (per this phase's scope — "do not build APIs yet"), so
it defines its own plain-Python exception hierarchy. A future service
layer that calls into this module can catch these and translate them
into AppException subclasses at that boundary, without this module ever
needing to know FastAPI exists.
"""


class ScanningError(Exception):
    """Base class for all errors raised by the scanning module."""


class InvalidScanRootError(ScanningError):
    """
    Raised when the folder handed to a scan doesn't exist or isn't
    actually a directory. Raised immediately, before any file is
    touched — failing fast on a bad root path is far more useful to a
    caller than silently returning zero results.
    """


class ImageMetadataExtractionError(ScanningError):
    """
    Raised when a file passed format validation (e.g. it's named
    photo.jpg) but its contents could not actually be read as an image
    — a truncated file, a renamed non-image file, corrupted data, etc.

    This is caught PER-FILE by ImageScanner, not allowed to propagate
    and abort an entire folder scan — one bad file should never block
    metadata extraction for the other 4,999 good ones.
    """
