"""
Tests for app/db/ (Phase 2): repositories, relationships, and the
cascade / set-null delete behavior the schema is designed around.
"""

from __future__ import annotations

from app.db.repositories import FaceRepository, PersonRepository, PhotoRepository


class TestPhotoRepository:
    def test_create_and_get(self, photo_repo: PhotoRepository) -> None:
        photo = photo_repo.create(file_path="/wedding/a.jpg")
        fetched = photo_repo.get(photo.id)
        assert fetched is not None
        assert fetched.file_path == "/wedding/a.jpg"

    def test_get_missing_returns_none(self, photo_repo: PhotoRepository) -> None:
        assert photo_repo.get(9999) is None

    def test_get_by_file_path(self, photo_repo: PhotoRepository) -> None:
        photo_repo.create(file_path="/wedding/a.jpg")
        found = photo_repo.get_by_file_path("/wedding/a.jpg")
        assert found is not None
        assert found.file_path == "/wedding/a.jpg"
        assert photo_repo.get_by_file_path("/wedding/does-not-exist.jpg") is None

    def test_get_by_file_hash_finds_duplicates(self, photo_repo: PhotoRepository) -> None:
        photo_repo.create(file_path="/a.jpg", file_hash="deadbeef")
        photo_repo.create(file_path="/b.jpg", file_hash="deadbeef")
        photo_repo.create(file_path="/c.jpg", file_hash="different")

        matches = photo_repo.get_by_file_hash("deadbeef")
        assert {p.file_path for p in matches} == {"/a.jpg", "/b.jpg"}

    def test_list_unprocessed_excludes_hashed_photos(self, photo_repo: PhotoRepository) -> None:
        photo_repo.create(file_path="/processed.jpg", file_hash="abc123")
        photo_repo.create(file_path="/unprocessed.jpg")

        unprocessed = photo_repo.list_unprocessed()
        assert [p.file_path for p in unprocessed] == ["/unprocessed.jpg"]

    def test_update_and_delete(self, photo_repo: PhotoRepository) -> None:
        photo = photo_repo.create(file_path="/a.jpg")
        updated = photo_repo.update(photo, quality_score=0.8)
        assert updated.quality_score == 0.8

        assert photo_repo.delete(photo.id) is True
        assert photo_repo.get(photo.id) is None
        assert photo_repo.delete(photo.id) is False  # already gone -> False, not an error


class TestPersonRepository:
    def test_list_by_ids_returns_only_matching_rows(self, person_repo: PersonRepository) -> None:
        alice = person_repo.create(display_name="Alice")
        person_repo.create(display_name="Bob")

        found = person_repo.list_by_ids([alice.id, 9999])
        assert [p.id for p in found] == [alice.id]

    def test_list_by_ids_empty_input_returns_empty(self, person_repo: PersonRepository) -> None:
        assert list(person_repo.list_by_ids([])) == []

    def test_confirmed_vs_unconfirmed_listing(self, person_repo: PersonRepository) -> None:
        person_repo.create(display_name="Confirmed", is_confirmed=True)
        person_repo.create(display_name=None, is_confirmed=False)

        assert len(person_repo.list_confirmed()) == 1
        assert len(person_repo.list_unconfirmed()) == 1


class TestRelationshipsAndCascades:
    """
    The schema's most important invariant, exercised directly:
    deleting a Photo cascades to its Faces (a face can't outlive its
    photo); deleting a Person only unlinks its Faces via SET NULL
    (a face detection is still real data even if its identity is
    forgotten).
    """

    def test_photo_faces_relationship_navigates_both_directions(
        self, photo_repo: PhotoRepository, face_repo: FaceRepository
    ) -> None:
        photo = photo_repo.create(file_path="/a.jpg")
        face = face_repo.create(photo_id=photo.id, bbox_x=0, bbox_y=0, bbox_width=10, bbox_height=10)

        assert face.photo.id == photo.id
        assert [f.id for f in photo.faces] == [face.id]

    def test_deleting_photo_cascades_to_faces(
        self, photo_repo: PhotoRepository, face_repo: FaceRepository
    ) -> None:
        photo = photo_repo.create(file_path="/a.jpg")
        face = face_repo.create(photo_id=photo.id, bbox_x=0, bbox_y=0, bbox_width=10, bbox_height=10)
        # Capture as a plain int BEFORE the delete: SQLAlchemy expires
        # ORM object attributes after a commit by default, and since the
        # face row itself is about to be cascade-deleted, touching
        # `face.id` again afterward would try to re-fetch a row that no
        # longer exists (ObjectDeletedError) rather than reflecting what
        # we actually want to assert here.
        face_id = face.id

        photo_repo.delete(photo.id)

        assert face_repo.get(face_id) is None

    def test_deleting_person_unlinks_but_does_not_delete_faces(
        self,
        photo_repo: PhotoRepository,
        face_repo: FaceRepository,
        person_repo: PersonRepository,
    ) -> None:
        photo = photo_repo.create(file_path="/a.jpg")
        person = person_repo.create(display_name="Alice")
        face = face_repo.create(
            photo_id=photo.id, person_id=person.id, bbox_x=0, bbox_y=0, bbox_width=10, bbox_height=10
        )

        person_repo.delete(person.id)

        remaining_face = face_repo.get(face.id)
        assert remaining_face is not None
        assert remaining_face.person_id is None

    def test_face_repository_list_by_photo_and_by_person(
        self,
        photo_repo: PhotoRepository,
        face_repo: FaceRepository,
        person_repo: PersonRepository,
    ) -> None:
        photo = photo_repo.create(file_path="/a.jpg")
        alice = person_repo.create(display_name="Alice")
        bob = person_repo.create(display_name="Bob")
        face_repo.create(photo_id=photo.id, person_id=alice.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1)
        face_repo.create(photo_id=photo.id, person_id=bob.id, bbox_x=1, bbox_y=1, bbox_width=1, bbox_height=1)

        assert len(face_repo.list_by_photo(photo.id)) == 2
        assert len(face_repo.list_by_person(alice.id)) == 1

    def test_list_unassigned_faces(self, photo_repo: PhotoRepository, face_repo: FaceRepository) -> None:
        photo = photo_repo.create(file_path="/a.jpg")
        face_repo.create(photo_id=photo.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1)  # unassigned

        unassigned = face_repo.list_unassigned()
        assert len(unassigned) == 1
        assert unassigned[0].person_id is None

    def test_assign_to_person(
        self,
        photo_repo: PhotoRepository,
        face_repo: FaceRepository,
        person_repo: PersonRepository,
    ) -> None:
        photo = photo_repo.create(file_path="/a.jpg")
        face = face_repo.create(photo_id=photo.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1)
        person = person_repo.create(display_name="Alice")

        updated = face_repo.assign_to_person(face.id, person.id)
        assert updated is not None
        assert updated.person_id == person.id

        cleared = face_repo.assign_to_person(face.id, None)
        assert cleared is not None
        assert cleared.person_id is None

    def test_assign_to_person_missing_face_returns_none(self, face_repo: FaceRepository) -> None:
        assert face_repo.assign_to_person(9999, 1) is None
