"""
Exceptions specific to the clustering module.

Same rationale as every other AI submodule: no HTTP awareness here — a
future service layer translates these into app/core/exceptions.py's
AppException subclasses at the API boundary.
"""


class ClusteringError(Exception):
    """Base class for all errors raised by the clustering module."""


class EmptyEmbeddingSetError(ClusteringError):
    """
    Raised when cluster() is called with zero embeddings. Clustering
    "nothing" isn't a meaningful operation with an empty-but-valid
    result — it almost always signals an upstream mistake (e.g. calling
    this before any faces have been embedded), so it's raised loudly
    rather than silently returning an empty ClusteringResult.
    """


class InconsistentEmbeddingModelError(ClusteringError):
    """
    Raised when the given embeddings weren't all produced by the same
    model (different model_name or dimension). Distances between
    embeddings from different models are meaningless numbers — see
    FaceEmbedding.cosine_similarity's own guard for the same rule at
    the pairwise level. This is that same guard, enforced once, up
    front, for an entire batch instead of embedding-pair by pair.
    """
