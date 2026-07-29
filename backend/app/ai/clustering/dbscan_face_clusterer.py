"""
DBSCAN face clustering implementation.
"""

from __future__ import annotations

import logging
from typing import Sequence

import numpy as np
from sklearn.cluster import DBSCAN

from app.ai.clustering.exceptions import EmptyEmbeddingSetError, InconsistentEmbeddingModelError
from app.ai.clustering.interfaces import FaceClustererBase, PersonLabelAssignerBase
from app.ai.clustering.models import ClusteringResult, EmbeddingRecord
from app.ai.clustering.person_label_assigner import PersonLabelAssigner


class DBSCANFaceClusterer(FaceClustererBase):
    """
    Groups face embeddings into candidate person clusters using
    scikit-learn's DBSCAN (Density-Based Spatial Clustering of
    Applications with Noise).

    See this module's top-level explanation for what DBSCAN is and why
    it was chosen over alternatives (e.g. k-means) for this problem.
    This class only handles running the algorithm and validating its
    input — turning the raw output into labeled PersonCluster objects
    is delegated to a PersonLabelAssignerBase (Single Responsibility).
    """

    def __init__(
        self,
        eps: float = 0.4,
        min_samples: int = 2,
        metric: str = "cosine",
        label_assigner: PersonLabelAssignerBase | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Args:
            eps: the maximum distance between two embeddings for them
                to be considered neighbors. With metric="cosine", this
                is a COSINE DISTANCE (1 - cosine_similarity), not a
                similarity — smaller eps means stricter matching. 0.4
                means two faces must have cosine similarity of at
                least 0.6 to ever be considered neighbors. See this
                module's explanation for how to tune this.
            min_samples: the minimum number of neighboring embeddings
                (including the point itself) required for a region to
                be considered "dense enough" to seed a cluster. 2 means
                a person needs to appear in at least 2 photos before
                DBSCAN will group them into a named cluster at all — a
                single appearance is always noise by construction (see
                this module's explanation of why that's the right
                default for a wedding photo library).
            metric: the distance metric DBSCAN uses. "cosine" matches
                how these embeddings were designed to be compared (see
                the Phase 5 face recognition module).
            label_assigner: converts raw DBSCAN output into named
                PersonCluster objects; defaults to PersonLabelAssigner.
            logger: optional logger; defaults to "app.ai.clustering".
        """
        self._eps = eps
        self._min_samples = min_samples
        self._metric = metric
        self._label_assigner = label_assigner or PersonLabelAssigner()
        self._logger = logger or logging.getLogger("app.ai.clustering")

    def cluster(self, records: Sequence[EmbeddingRecord]) -> ClusteringResult:
        """
        Args:
            records: every embedding to cluster together.

        Returns:
            A ClusteringResult with "Person N" clusters and a list of
            unknown (noise) face identifiers.

        Raises:
            EmptyEmbeddingSetError: if `records` is empty.
            InconsistentEmbeddingModelError: if the embeddings weren't
                all produced by the same model/dimension.
        """
        if not records:
            raise EmptyEmbeddingSetError("Cannot cluster an empty set of embeddings.")

        self._validate_consistent_embeddings(records)

        # Stack every embedding's vector into one (N, 512) matrix —
        # the shape scikit-learn's DBSCAN expects.
        vectors = np.stack([record.embedding.vector for record in records])

        dbscan = DBSCAN(eps=self._eps, min_samples=self._min_samples, metric=self._metric)
        # fit_predict runs the full algorithm and returns one integer
        # label per input row: 0, 1, 2, ... per discovered cluster, or
        # -1 for a point DBSCAN considers noise. See this module's
        # explanation for exactly how these labels are formed.
        raw_labels = dbscan.fit_predict(vectors)

        result = self._label_assigner.assign(records, raw_labels)

        self._logger.info(
            "Clustering complete: %d embedding(s) -> %d person(s), %d unknown face(s)",
            len(records),
            result.total_persons_found,
            result.total_unknown_faces,
        )
        return result

    @staticmethod
    def _validate_consistent_embeddings(records: Sequence[EmbeddingRecord]) -> None:
        """
        Guard against silently clustering embeddings that came from
        different models or have mismatched dimensions — the resulting
        distances would be numbers, but not meaningful ones.
        """
        model_names = {record.embedding.model_name for record in records}
        if len(model_names) > 1:
            raise InconsistentEmbeddingModelError(
                f"Cannot cluster embeddings produced by different models: {sorted(model_names)}"
            )

        dimensions = {record.embedding.dimension for record in records}
        if len(dimensions) > 1:
            raise InconsistentEmbeddingModelError(
                f"Cannot cluster embeddings with different dimensions: {sorted(dimensions)}"
            )
