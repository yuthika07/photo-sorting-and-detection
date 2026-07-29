"""
FaceClusteringService — the reusable, high-level entry point for this
module.
"""

from __future__ import annotations

import logging
from typing import Sequence

from app.ai.clustering.interfaces import FaceClustererBase
from app.ai.clustering.models import ClusteringResult, EmbeddingRecord


class FaceClusteringService:
    """
    Thin, reusable wrapper around a FaceClustererBase.

    Kept intentionally small: unlike face detection/recognition, there
    is no expensive one-time model to load here — DBSCAN has no
    "weights," it's a plain algorithm run fresh on whatever embeddings
    are handed to it. This service exists mainly for interface
    consistency with the rest of the AI pipeline (every stage exposes
    a *Service as its main entry point) and as the natural place to add
    cross-cutting behavior later (e.g. logging, timing, or comparing
    results across multiple parameter choices) without touching the
    clustering algorithm itself.
    """

    def __init__(self, clusterer: FaceClustererBase, logger: logging.Logger | None = None) -> None:
        """
        Args:
            clusterer: the clustering algorithm implementation to use.
            logger: optional logger; defaults to "app.ai.clustering".
        """
        self._clusterer = clusterer
        self._logger = logger or logging.getLogger("app.ai.clustering")

    def cluster(self, records: Sequence[EmbeddingRecord]) -> ClusteringResult:
        """
        Args:
            records: every embedding to cluster, each tagged with the
                caller's own identifier (e.g. a Face.id).

        Returns:
            A ClusteringResult: discovered "Person N" clusters plus a
            list of unknown (noise) face identifiers.
        """
        return self._clusterer.cluster(records)
