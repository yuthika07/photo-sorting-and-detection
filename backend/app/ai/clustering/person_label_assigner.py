"""
Concrete person-label assignment implementation.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Sequence

import numpy as np

from app.ai.clustering.interfaces import PersonLabelAssignerBase
from app.ai.clustering.models import ClusteringResult, EmbeddingRecord, PersonCluster

#: DBSCAN's fixed convention: any point it couldn't fit into a dense
#: enough neighborhood is labeled exactly -1. Not something we choose.
NOISE_LABEL = -1


class PersonLabelAssigner(PersonLabelAssignerBase):
    """
    Converts DBSCAN's raw integer cluster labels into ordered,
    human-readable "Person N" identifiers.

    Two things this class deliberately owns, kept separate from the
    clustering algorithm itself (Single Responsibility):

    1. Separating noise (-1) from real clusters, and returning noise
       identifiers as `unknown_face_identifiers` rather than a cluster.
    2. Renumbering clusters by descending size, so "Person 1" is
       whichever candidate person appears in the most photos — a
       meaningful, deterministic order — rather than DBSCAN's raw
       label order, which depends only on the arbitrary order points
       happened to be visited in and carries no real meaning.
    """

    def assign(self, records: Sequence[EmbeddingRecord], raw_labels: np.ndarray) -> ClusteringResult:
        """
        Args:
            records: the records clustering was run on.
            raw_labels: DBSCAN's per-record integer labels, same order
                as `records`.

        Returns:
            A ClusteringResult with "Person 1", "Person 2", ... labels
            ordered largest-cluster-first, and every noise point
            collected into `unknown_face_identifiers`.
        """
        # Group identifiers by their raw DBSCAN label first; noise
        # points (-1) are pulled out into their own list rather than
        # treated as "cluster -1".
        raw_groups: dict[int, list[int]] = defaultdict(list)
        unknown_identifiers: list[int] = []

        for record, raw_label in zip(records, raw_labels):
            label = int(raw_label)
            if label == NOISE_LABEL:
                unknown_identifiers.append(record.identifier)
            else:
                raw_groups[label].append(record.identifier)

        # Sort by descending cluster size (most-photographed person
        # first); break ties by raw label for a fully deterministic,
        # reproducible ordering given the same input every time.
        ordered_groups = sorted(raw_groups.items(), key=lambda item: (-len(item[1]), item[0]))

        person_clusters = tuple(
            PersonCluster(
                person_label=f"Person {position}",
                cluster_id=raw_label,
                member_identifiers=tuple(member_identifiers),
            )
            for position, (raw_label, member_identifiers) in enumerate(ordered_groups, start=1)
        )

        return ClusteringResult(
            person_clusters=person_clusters,
            unknown_face_identifiers=tuple(unknown_identifiers),
        )
