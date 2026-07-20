"""
Concrete embedding serialization implementation.
"""

from __future__ import annotations

import numpy as np

from app.ai.face_recognition.interfaces import EmbeddingSerializerBase
from app.ai.face_recognition.models import FaceEmbedding


class NumpyEmbeddingSerializer(EmbeddingSerializerBase):
    """
    Converts a FaceEmbedding's vector to/from raw float32 bytes.

    A 512-dimensional float32 vector serializes to exactly 512 * 4 =
    2048 bytes — small enough to store directly as a BLOB, which is
    exactly the shape of the Face.embedding column defined in Phase 2's
    database layer (a SQLAlchemy LargeBinary field). This class is what
    makes a FaceEmbedding storable there without either module needing
    to know about the other's internals.
    """

    def to_bytes(self, embedding: FaceEmbedding) -> bytes:
        """
        Args:
            embedding: the embedding to serialize.

        Returns:
            Raw float32 bytes (2048 bytes for a 512-d vector), ready to
            store in a BLOB/LargeBinary column.
        """
        # .astype(np.float32) guarantees a consistent byte width even
        # if some future model produced float64 internally — storage
        # size and format stay predictable regardless of the source.
        return embedding.vector.astype(np.float32).tobytes()

    def from_bytes(self, data: bytes, model_name: str) -> FaceEmbedding:
        """
        Args:
            data: raw float32 bytes, as produced by to_bytes().
            model_name: which model produced this embedding — must be
                supplied by the caller, since the identifier isn't
                encoded in the raw bytes themselves. Storage of this
                metadata is the caller's/EmbeddingStoreBase's concern.

        Returns:
            A reconstructed FaceEmbedding.
        """
        # np.frombuffer returns a READ-ONLY view directly over `data`.
        # We .copy() it so the resulting array owns its own memory —
        # otherwise FaceEmbedding.__post_init__'s setflags(write=False)
        # would be redundant, but more importantly the array's lifetime
        # would stay tied to the original `data` bytes object in a way
        # that's easy to get wrong later.
        vector = np.frombuffer(data, dtype=np.float32).copy()
        return FaceEmbedding(vector=vector, dimension=vector.shape[0], model_name=model_name)
