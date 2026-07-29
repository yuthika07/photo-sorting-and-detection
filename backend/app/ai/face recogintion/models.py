"""
Data model returned by the face recognition module.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FaceEmbedding:
    """
    A single face's identity, represented as a fixed-length numeric
    vector — the "reusable object" this module is asked to return.

    Deliberately carries `model_name` alongside the vector itself: an
    embedding is only meaningful relative to the specific model that
    produced it (see this phase's explanation on why vectors represent
    identity). Comparing an embedding from ArcFace against one from a
    different model would produce a meaningless number, so tagging
    every embedding with its origin lets later code (a similarity
    check, a future clustering stage) refuse to compare mismatched
    embeddings instead of silently producing garbage.
    """

    vector: np.ndarray
    dimension: int
    model_name: str

    def __post_init__(self) -> None:
        """
        Validate shape and lock the underlying array against mutation.

        `frozen=True` on the dataclass only stops `self.vector = ...`
        reassignment — it does NOT stop someone calling
        `embedding.vector[0] = 999` to mutate the array's contents in
        place. `setflags(write=False)` closes that gap: any attempt to
        write into the array after construction raises a ValueError,
        making this object genuinely immutable, not just
        "immutable-looking."
        """
        if self.vector.ndim != 1 or self.vector.shape[0] != self.dimension:
            raise ValueError(
                f"Embedding vector must be 1-dimensional with shape "
                f"({self.dimension},), got shape {self.vector.shape}"
            )
        self.vector.setflags(write=False)

    def cosine_similarity(self, other: "FaceEmbedding") -> float:
        """
        Compare this embedding against another, returning a score from
        -1.0 (opposite) to 1.0 (identical direction).

        Because embeddings are L2-normalized at generation time (see
        ArcFaceEmbedder), cosine similarity between two unit vectors
        simplifies to a plain dot product — no need to divide by the
        vectors' magnitudes, since both are already exactly 1.0. This
        is why normalization happens once, up front, at generation time
        rather than being recomputed on every comparison: it turns
        every future similarity check into one cheap dot product.

        Args:
            other: another FaceEmbedding to compare against.

        Raises:
            ValueError: if the two embeddings came from different
                models or have mismatched dimensions — comparing them
                would produce a number, but not a meaningful one.
        """
        if self.model_name != other.model_name:
            raise ValueError(
                f"Cannot compare embeddings from different models: "
                f"{self.model_name!r} vs {other.model_name!r}"
            )
        if self.dimension != other.dimension:
            raise ValueError(
                f"Cannot compare embeddings of different dimensions: "
                f"{self.dimension} vs {other.dimension}"
            )
        return float(np.dot(self.vector, other.vector))
