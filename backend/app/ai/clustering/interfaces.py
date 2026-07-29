"""
Abstract interfaces for the clustering module's collaborators.

Same SOLID pattern as every prior AI submodule.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

import numpy as np

from app.ai.clustering.models import ClusteringResult, EmbeddingRecord


class FaceClustererBase(ABC):
    """
    Contract for grouping a batch of embeddings into candidate person
    clusters. Knows nothing about how those clusters get human-readable
    labels — that's PersonLabelAssignerBase's job (Single Responsibility).
    """

    @abstractmethod
    def cluster(self, records: Sequence[EmbeddingRecord]) -> ClusteringResult:
        """
        Args:
            records: every embedding to cluster together, each tagged
                with the caller's own identifier.

        Returns:
            A ClusteringResult with discovered person clusters and a
            list of unknown (noise) face identifiers.

        Raises:
            EmptyEmbeddingSetError: if `records` is empty.
            InconsistentEmbeddingModelError: if the embeddings weren't
                all produced by the same model.
        """
        raise NotImplementedError


class PersonLabelAssignerBase(ABC):
    """
    Contract for turning a clustering algorithm's raw output (which
    record belongs to which raw integer label, including -1 for noise)
    into a ClusteringResult with meaningful "Person N" labels.
    """

    @abstractmethod
    def assign(self, records: Sequence[EmbeddingRecord], raw_labels: np.ndarray) -> ClusteringResult:
        """
        Args:
            records: the same records that were passed into clustering,
                in the same order as `raw_labels`.
            raw_labels: one integer per record — the clustering
                algorithm's raw cluster assignment (-1 means noise).

        Returns:
            A ClusteringResult with stable, human-readable person labels.
        """
        raise NotImplementedError
