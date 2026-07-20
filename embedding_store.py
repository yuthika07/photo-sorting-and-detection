"""
Concrete embedding storage implementation, built on top of the Phase 2
database layer.
"""

from __future__ import annotations

from app.ai.face_recognition.exceptions import FaceRecognitionError
from app.ai.face_recognition.interfaces import EmbeddingSerializerBase, EmbeddingStoreBase
from app.ai.face_recognition.models import FaceEmbedding
from app.db.repositories import FaceRepository


class SQLiteFaceEmbeddingStore(EmbeddingStoreBase):
    """
    Persists a FaceEmbedding into an existing Face row's `embedding`
    column, and reads it back out.

    Deliberately reuses Phase 2's FaceRepository rather than talking to
    SQLAlchemy directly -- this module has no idea what a database
    session or a Face ORM model even is beyond what FaceRepository
    exposes, keeping the recognition module's only coupling to the
    persistence layer confined to this one class (everything else in
    this module -- the embedder, the aligner, the serializer -- has zero
    database awareness and could be unit tested with no DB at all).
    """

    def __init__(
        self,
        face_repository: FaceRepository,
        serializer: EmbeddingSerializerBase,
        model_name: str,
    ) -> None:
        """
        Args:
            face_repository: the Phase 2 repository used to read/write
                Face rows.
            serializer: converts a FaceEmbedding to/from the raw bytes
                actually stored in the Face.embedding column.
            model_name: which model's embeddings this store deals in.
                Not stored in the Face row itself (Phase 2's schema has
                no `embedding_model` column) -- this class is the single
                source of truth for that label when reconstructing a
                FaceEmbedding on load(). A future migration could add
                that column if multiple models are ever used side by
                side; not needed yet, so not built prematurely.
        """
        self._face_repository = face_repository
        self._serializer = serializer
        self._model_name = model_name

    def save(self, face_id: int, embedding: FaceEmbedding) -> None:
        """
        Args:
            face_id: the id of an existing Face row.
            embedding: the embedding to store against it.

        Raises:
            FaceRecognitionError: if no Face row with that id exists --
                an embedding can never meaningfully exist without the
                face detection it was derived from.
        """
        face = self._face_repository.get(face_id)
        if face is None:
            raise FaceRecognitionError(
                f"Cannot store embedding: no Face row with id={face_id} exists."
            )

        serialized = self._serializer.to_bytes(embedding)
        self._face_repository.update(face, embedding=serialized)

    def load(self, face_id: int) -> FaceEmbedding | None:
        """
        Args:
            face_id: the id of a Face row.

        Returns:
            The stored FaceEmbedding, or None if the Face doesn't exist
            or hasn't had an embedding stored yet (Face.embedding is
            nullable -- see the Phase 2 schema).
        """
        face = self._face_repository.get(face_id)
        if face is None or face.embedding is None:
            return None

        return self._serializer.from_bytes(face.embedding, model_name=self._model_name)
