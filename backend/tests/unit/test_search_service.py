"""
Tests for app/services/photo_search_service.py (Phase 7).
"""

from __future__ import annotations

import pytest

from app.core.exceptions import NotFoundError
from app.db.repositories import FaceRepository, PersonRepository, PhotoRepository
from app.services.photo_search_service import PhotoSearchService


@pytest.fixture()
def seeded_wedding(
    photo_repo: PhotoRepository, face_repo: FaceRepository, person_repo: PersonRepository
):
    """
    Alice, Bob, Carol across 5 photos:
      photo1: Alice only
      photo2: Bob only
      photo3: Alice + Bob
      photo4: Alice + Bob + Carol
      photo5: Carol only
    """
    alice = person_repo.create(display_name="Alice")
    bob = person_repo.create(display_name="Bob")
    carol = person_repo.create(display_name="Carol")

    photo1 = photo_repo.create(file_path="/p1.jpg")
    photo2 = photo_repo.create(file_path="/p2.jpg")
    photo3 = photo_repo.create(file_path="/p3.jpg")
    photo4 = photo_repo.create(file_path="/p4.jpg")
    photo5 = photo_repo.create(file_path="/p5.jpg")

    def face(photo_id: int, person_id: int) -> None:
        face_repo.create(photo_id=photo_id, person_id=person_id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1)

    face(photo1.id, alice.id)
    face(photo2.id, bob.id)
    face(photo3.id, alice.id)
    face(photo3.id, bob.id)
    face(photo4.id, alice.id)
    face(photo4.id, bob.id)
    face(photo4.id, carol.id)
    face(photo5.id, carol.id)

    return {"alice": alice, "bob": bob, "carol": carol}


class TestPhotoSearchService:
    def test_search_by_single_person(self, seeded_wedding, photo_repo, person_repo) -> None:
        service = PhotoSearchService(person_repo, photo_repo)
        _, photos = service.search_by_persons([seeded_wedding["alice"].id])
        assert {p.file_path for p in photos} == {"/p1.jpg", "/p3.jpg", "/p4.jpg"}

    def test_search_by_two_people_requires_both(self, seeded_wedding, photo_repo, person_repo) -> None:
        service = PhotoSearchService(person_repo, photo_repo)
        _, photos = service.search_by_persons([seeded_wedding["alice"].id, seeded_wedding["bob"].id])
        assert {p.file_path for p in photos} == {"/p3.jpg", "/p4.jpg"}

    def test_search_by_three_people_requires_all_three(self, seeded_wedding, photo_repo, person_repo) -> None:
        service = PhotoSearchService(person_repo, photo_repo)
        _, photos = service.search_by_persons(
            [seeded_wedding["alice"].id, seeded_wedding["bob"].id, seeded_wedding["carol"].id]
        )
        assert {p.file_path for p in photos} == {"/p4.jpg"}

    def test_search_returns_resolved_person_objects(self, seeded_wedding, photo_repo, person_repo) -> None:
        service = PhotoSearchService(person_repo, photo_repo)
        persons, _ = service.search_by_persons([seeded_wedding["alice"].id])
        assert [p.display_name for p in persons] == ["Alice"]

    def test_search_with_unknown_person_id_raises_not_found(self, seeded_wedding, photo_repo, person_repo) -> None:
        service = PhotoSearchService(person_repo, photo_repo)
        with pytest.raises(NotFoundError) as exc_info:
            service.search_by_persons([9999])
        assert exc_info.value.details["missing_person_ids"] == [9999]

    def test_partial_unknown_ids_reports_only_the_missing_one(
        self, seeded_wedding, photo_repo, person_repo
    ) -> None:
        service = PhotoSearchService(person_repo, photo_repo)
        with pytest.raises(NotFoundError) as exc_info:
            service.search_by_persons([seeded_wedding["alice"].id, 9999])
        assert exc_info.value.details["missing_person_ids"] == [9999]

    def test_search_for_person_with_no_photos_returns_empty(self, photo_repo, person_repo) -> None:
        lonely = person_repo.create(display_name="Nobody's photos")
        service = PhotoSearchService(person_repo, photo_repo)
        _, photos = service.search_by_persons([lonely.id])
        assert photos == []

    def test_duplicate_person_ids_in_request_are_deduplicated(
        self, seeded_wedding, photo_repo, person_repo
    ) -> None:
        service = PhotoSearchService(person_repo, photo_repo)
        alice_id = seeded_wedding["alice"].id
        _, photos = service.search_by_persons([alice_id, alice_id, alice_id])
        # requesting the same person 3x must not require 3 distinct matches per photo
        assert {p.file_path for p in photos} == {"/p1.jpg", "/p3.jpg", "/p4.jpg"}
