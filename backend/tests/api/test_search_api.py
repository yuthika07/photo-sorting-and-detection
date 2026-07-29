"""
Tests for GET /search/photos (Phase 7), exercised over real HTTP via
FastAPI's TestClient rather than calling the service directly — this
is what actually proves request parsing, dependency injection, and the
main.py exception-handler wiring all work together end to end.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.repositories import FaceRepository, PersonRepository, PhotoRepository


def seed_alice_bob(photo_repo: PhotoRepository, face_repo: FaceRepository, person_repo: PersonRepository):
    alice = person_repo.create(display_name="Alice")
    bob = person_repo.create(display_name="Bob")
    solo = photo_repo.create(file_path="/alice_solo.jpg")
    together = photo_repo.create(file_path="/together.jpg")

    face_repo.create(photo_id=solo.id, person_id=alice.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1)
    face_repo.create(photo_id=together.id, person_id=alice.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1)
    face_repo.create(photo_id=together.id, person_id=bob.id, bbox_x=5, bbox_y=5, bbox_width=1, bbox_height=1)

    return alice, bob


class TestSearchPhotosEndpoint:
    def test_search_single_person(
        self, client: TestClient, photo_repo: PhotoRepository, face_repo: FaceRepository, person_repo: PersonRepository
    ) -> None:
        alice, _ = seed_alice_bob(photo_repo, face_repo, person_repo)

        response = client.get("/search/photos", params={"person_ids": [alice.id]})

        assert response.status_code == 200
        body = response.json()
        assert body["total_photos"] == 2
        assert body["persons"] == [{"id": alice.id, "display_name": "Alice"}]

    def test_search_multiple_people_and_semantics(
        self, client: TestClient, photo_repo: PhotoRepository, face_repo: FaceRepository, person_repo: PersonRepository
    ) -> None:
        alice, bob = seed_alice_bob(photo_repo, face_repo, person_repo)

        response = client.get("/search/photos", params={"person_ids": [alice.id, bob.id]})

        assert response.status_code == 200
        body = response.json()
        assert body["total_photos"] == 1
        assert body["photos"][0]["file_path"] == "/together.jpg"

    def test_search_missing_person_ids_param_returns_422(self, client: TestClient) -> None:
        response = client.get("/search/photos")
        assert response.status_code == 422

    def test_search_unknown_person_id_returns_404_with_standard_envelope(self, client: TestClient) -> None:
        response = client.get("/search/photos", params={"person_ids": [999]})

        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "NOT_FOUND"
        assert body["error"]["details"]["missing_person_ids"] == [999]

    def test_search_person_with_no_matching_photos_returns_empty_list(
        self, client: TestClient, person_repo: PersonRepository
    ) -> None:
        lonely = person_repo.create(display_name="Lonely")
        response = client.get("/search/photos", params={"person_ids": [lonely.id]})

        assert response.status_code == 200
        assert response.json()["photos"] == []
