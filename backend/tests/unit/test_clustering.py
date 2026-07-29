"""
Tests for app/ai/clustering/ (Phase 6). DBSCAN has no model weights,
so every test here is fast and fully deterministic.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.ai.clustering.dbscan_face_clusterer import DBSCANFaceClusterer
from app.ai.clustering.exceptions import EmptyEmbeddingSetError, InconsistentEmbeddingModelError
from app.ai.clustering.face_clustering_service import FaceClusteringService
from app.ai.clustering.models import EmbeddingRecord
from app.ai.face_recognition.models import FaceEmbedding


def unit_vector_near(person_index: int, dimension: int = 8, noise: float = 0.02, rng_seed: int = 0) -> np.ndarray:
    """
    Build a unit vector representing "another photo of person #person_index".

    Uses an orthogonal one-hot basis vector per person (guaranteeing
    cosine distance of exactly 1.0 between different people) rather
    than two independent random vectors, which — in a deliberately
    small test dimensionality — can occasionally land close together
    purely by chance and make the test flaky for reasons that have
    nothing to do with the clustering code under test.
    """
    base = np.zeros(dimension, dtype=np.float64)
    base[person_index % dimension] = 1.0

    noise_rng = np.random.default_rng(rng_seed)
    perturbed = base + noise_rng.normal(scale=noise, size=dimension)
    return (perturbed / np.linalg.norm(perturbed)).astype(np.float32)


def embedding(vector: np.ndarray, model_name: str = "test-model") -> FaceEmbedding:
    return FaceEmbedding(vector=vector, dimension=vector.shape[0], model_name=model_name)


class TestDBSCANFaceClusterer:
    def test_raises_on_empty_input(self) -> None:
        with pytest.raises(EmptyEmbeddingSetError):
            DBSCANFaceClusterer().cluster([])

    def test_raises_on_mismatched_models(self) -> None:
        a = embedding(unit_vector_near(1, rng_seed=1), model_name="model-a")
        b = embedding(unit_vector_near(1, rng_seed=2), model_name="model-b")
        with pytest.raises(InconsistentEmbeddingModelError):
            DBSCANFaceClusterer().cluster([EmbeddingRecord(1, a), EmbeddingRecord(2, b)])

    def test_raises_on_mismatched_dimensions(self) -> None:
        a = embedding(unit_vector_near(1, dimension=8, rng_seed=1))
        b = embedding(unit_vector_near(1, dimension=16, rng_seed=2))
        with pytest.raises(InconsistentEmbeddingModelError):
            DBSCANFaceClusterer().cluster([EmbeddingRecord(1, a), EmbeddingRecord(2, b)])

    def test_groups_similar_embeddings_into_one_person(self) -> None:
        records = [
            EmbeddingRecord(1, embedding(unit_vector_near(100, rng_seed=1))),
            EmbeddingRecord(2, embedding(unit_vector_near(100, rng_seed=2))),
            EmbeddingRecord(3, embedding(unit_vector_near(100, rng_seed=3))),
        ]
        result = DBSCANFaceClusterer(eps=0.4, min_samples=2).cluster(records)

        assert result.total_persons_found == 1
        assert result.total_unknown_faces == 0
        assert set(result.person_clusters[0].member_identifiers) == {1, 2, 3}

    def test_dissimilar_single_appearances_become_unknown(self) -> None:
        records = [
            EmbeddingRecord(1, embedding(unit_vector_near(1, rng_seed=1))),
            EmbeddingRecord(2, embedding(unit_vector_near(2, rng_seed=2))),
            EmbeddingRecord(3, embedding(unit_vector_near(3, rng_seed=3))),
        ]
        result = DBSCANFaceClusterer(eps=0.4, min_samples=2).cluster(records)

        # each face appears once -> min_samples=2 can never be satisfied -> all noise
        assert result.total_persons_found == 0
        assert set(result.unknown_face_identifiers) == {1, 2, 3}

    def test_mixed_scenario_clusters_and_unknowns_together(self) -> None:
        records = [
            EmbeddingRecord(1, embedding(unit_vector_near(10, rng_seed=1))),  # person A, photo 1
            EmbeddingRecord(2, embedding(unit_vector_near(10, rng_seed=2))),  # person A, photo 2
            EmbeddingRecord(3, embedding(unit_vector_near(10, rng_seed=3))),  # person A, photo 3
            EmbeddingRecord(4, embedding(unit_vector_near(20, rng_seed=4))),  # person B, photo 1
            EmbeddingRecord(5, embedding(unit_vector_near(20, rng_seed=5))),  # person B, photo 2
            EmbeddingRecord(6, embedding(unit_vector_near(30, rng_seed=6))),  # lone stranger
        ]
        result = DBSCANFaceClusterer(eps=0.4, min_samples=2).cluster(records)

        assert result.total_persons_found == 2
        # "Person 1" is the larger cluster (3 members), deterministically
        assert result.person_clusters[0].person_label == "Person 1"
        assert result.person_clusters[0].size == 3
        assert result.person_clusters[1].person_label == "Person 2"
        assert result.person_clusters[1].size == 2
        assert result.unknown_face_identifiers == (6,)

    def test_labeling_is_order_independent(self) -> None:
        """Searching 'Bob + Alice' vs 'Alice + Bob' shouldn't matter for clustering order."""
        records_a = [
            EmbeddingRecord(1, embedding(unit_vector_near(10, rng_seed=1))),
            EmbeddingRecord(2, embedding(unit_vector_near(10, rng_seed=2))),
        ]
        records_b = list(reversed(records_a))

        result_a = DBSCANFaceClusterer(eps=0.4, min_samples=2).cluster(records_a)
        result_b = DBSCANFaceClusterer(eps=0.4, min_samples=2).cluster(records_b)

        assert set(result_a.person_clusters[0].member_identifiers) == set(
            result_b.person_clusters[0].member_identifiers
        )


class TestFaceClusteringService:
    def test_delegates_to_clusterer(self) -> None:
        service = FaceClusteringService(DBSCANFaceClusterer(eps=0.4, min_samples=2))
        records = [
            EmbeddingRecord(1, embedding(unit_vector_near(1, rng_seed=1))),
            EmbeddingRecord(2, embedding(unit_vector_near(1, rng_seed=2))),
        ]
        result = service.cluster(records)
        assert result.total_persons_found == 1
