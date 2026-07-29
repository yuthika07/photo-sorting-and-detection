"""
Data models for the clustering module.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.face_recognition.models import FaceEmbedding


@dataclass(frozen=True)
class EmbeddingRecord:
    """
    One embedding to cluster, tagged with the caller's own identifier
    (e.g. a Face.id from the Phase 2 database) so cluster results can be
    mapped back to real faces afterward.

    This module never touches the database itself — it doesn't know
    what a "Face row" is — `identifier` is deliberately just a plain
    int the caller assigns meaning to. That keeps this module reusable
    for clustering embeddings from any source, not just SQLite-backed
    Face rows.
    """

    identifier: int
    embedding: FaceEmbedding


@dataclass(frozen=True)
class PersonCluster:
    """
    One group of embeddings DBSCAN decided are visually similar enough
    to represent a single, recurring person.

    This is a CANDIDATE person, not a confirmed identity — matching the
    Phase 2 Person model's `is_confirmed` field, which defaults to
    False until a human verifies the grouping is actually correct.
    """

    #: Human-facing label, e.g. "Person 1". See PersonLabelAssigner for
    #: how this is assigned and why the numbering is meaningful, not
    #: arbitrary.
    person_label: str

    #: DBSCAN's own raw integer cluster label (0, 1, 2, ...) — kept
    #: around for debugging/traceability, but nothing outside this
    #: module should depend on its specific value or ordering.
    cluster_id: int

    #: The caller-supplied identifiers (see EmbeddingRecord) of every
    #: embedding DBSCAN placed in this cluster.
    member_identifiers: tuple[int, ...]

    @property
    def size(self) -> int:
        """How many faces this candidate person appears in."""
        return len(self.member_identifiers)


@dataclass(frozen=True)
class ClusteringResult:
    """
    The full output of one clustering run: every discovered person
    cluster, plus every face that didn't fit into any of them.
    """

    person_clusters: tuple[PersonCluster, ...]

    #: Identifiers of faces DBSCAN marked as noise — see this module's
    #: explanation of what "noise" means. These are NOT dropped; they
    #: are returned explicitly so a caller can decide what to do with
    #: them (e.g. leave Face.person_id as NULL, exactly as Phase 2's
    #: schema already supports, and surface them for manual review).
    unknown_face_identifiers: tuple[int, ...]

    @property
    def total_persons_found(self) -> int:
        """How many distinct candidate people were discovered."""
        return len(self.person_clusters)

    @property
    def total_unknown_faces(self) -> int:
        """How many faces could not be confidently grouped with any other."""
        return len(self.unknown_face_identifiers)
