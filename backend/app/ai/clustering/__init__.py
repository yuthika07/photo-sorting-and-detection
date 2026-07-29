"""
Clustering module — groups a batch of face embeddings into candidate
"Person 1", "Person 2", ... clusters using DBSCAN, explicitly separating
out faces that don't confidently belong to any group ("unknown" faces).

Self-contained like the other AI submodules: takes a list of
EmbeddingRecord in, returns a ClusteringResult out. No database
awareness — a future service is responsible for turning each
PersonCluster into a Person row (via PersonRepository) and updating
each member Face's person_id (via FaceRepository), and for deciding
what to do with unknown_face_identifiers (Phase 2's schema already
supports leaving Face.person_id as NULL for exactly this case).

Structure:

    exceptions.py                  -> ClusteringError hierarchy
    models.py                       -> EmbeddingRecord, PersonCluster, ClusteringResult
    interfaces.py                     -> abstract collaborator contracts (ABCs)
    person_label_assigner.py            -> PersonLabelAssigner ("Person N" naming + noise handling)
    dbscan_face_clusterer.py              -> DBSCANFaceClusterer (runs the algorithm)
    face_clustering_service.py              -> FaceClusteringService (the reusable service)

Quick start:

    from app.ai.clustering import create_default_face_clustering_service
    from app.ai.clustering.models import EmbeddingRecord

    records = [EmbeddingRecord(identifier=face.id, embedding=emb) for face, emb in ...]
    service = create_default_face_clustering_service()
    result = service.cluster(records)

    for person in result.person_clusters:
        print(person.person_label, "->", person.member_identifiers)
    print("Unknown faces:", result.unknown_face_identifiers)
"""

from app.ai.clustering.dbscan_face_clusterer import DBSCANFaceClusterer
from app.ai.clustering.exceptions import (
    ClusteringError,
    EmptyEmbeddingSetError,
    InconsistentEmbeddingModelError,
)
from app.ai.clustering.face_clustering_service import FaceClusteringService
from app.ai.clustering.models import ClusteringResult, EmbeddingRecord, PersonCluster
from app.ai.clustering.person_label_assigner import PersonLabelAssigner
from app.core.config import get_settings


def create_default_face_clustering_service() -> FaceClusteringService:
    """
    Convenience factory wiring up a FaceClusteringService using this
    project's configured eps/min_samples settings (see
    clustering_eps / clustering_min_samples in core/config.py) and the
    default concrete implementations.
    """
    settings = get_settings()
    clusterer = DBSCANFaceClusterer(
        eps=settings.clustering_eps,
        min_samples=settings.clustering_min_samples,
    )
    return FaceClusteringService(clusterer=clusterer)


__all__ = [
    "FaceClusteringService",
    "DBSCANFaceClusterer",
    "PersonLabelAssigner",
    "EmbeddingRecord",
    "PersonCluster",
    "ClusteringResult",
    "ClusteringError",
    "EmptyEmbeddingSetError",
    "InconsistentEmbeddingModelError",
    "create_default_face_clustering_service",
]
