"""
Tests for app/services/export/ (Phase 8). Uses real files on disk via
tmp_path — this module's whole job is file I/O, so faking the
filesystem would test nothing meaningful.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.db.repositories import FaceRepository, PersonRepository, PhotoRepository
from app.services.export.exceptions import InvalidDestinationError
from app.services.export.file_copier import SafeFileCopier
from app.services.export.folder_namer import PersonFolderNamer
from app.services.export.photo_export_service import PhotoExportService
from app.services.photo_search_service import PhotoSearchService


@pytest.fixture()
def export_service(
    person_repo: PersonRepository, photo_repo: PhotoRepository
) -> PhotoExportService:
    search_service = PhotoSearchService(person_repo, photo_repo)
    return PhotoExportService(
        search_service=search_service, folder_namer=PersonFolderNamer(), file_copier=SafeFileCopier()
    )


class TestPersonFolderNamer:
    def test_single_person_uses_display_name(self, person_repo: PersonRepository) -> None:
        alice = person_repo.create(display_name="Alice")
        name = PersonFolderNamer().build_folder_name([alice])
        assert name == "Alice"

    def test_multiple_people_joined_with_underscore(self, person_repo: PersonRepository) -> None:
        alice = person_repo.create(display_name="Alice")
        bob = person_repo.create(display_name="Bob")
        name = PersonFolderNamer().build_folder_name([alice, bob])
        assert name == "Alice_Bob"

    def test_order_independent(self, person_repo: PersonRepository) -> None:
        alice = person_repo.create(display_name="Alice")
        bob = person_repo.create(display_name="Bob")
        assert PersonFolderNamer().build_folder_name([alice, bob]) == PersonFolderNamer().build_folder_name(
            [bob, alice]
        )

    def test_unnamed_person_falls_back_to_id(self, person_repo: PersonRepository) -> None:
        person = person_repo.create(display_name=None)
        name = PersonFolderNamer().build_folder_name([person])
        assert name == f"Person_{person.id}"

    def test_sanitizes_unsafe_characters(self, person_repo: PersonRepository) -> None:
        person = person_repo.create(display_name="Bride & Groom / Reception")
        name = PersonFolderNamer().build_folder_name([person])
        assert "/" not in name
        assert "&" not in name


class TestSafeFileCopier:
    def test_preserves_original_filename(self, tmp_path: Path, make_image) -> None:
        source = make_image("photo.jpg", subdir="source")
        destination_dir = tmp_path / "dest"

        result_path = SafeFileCopier().copy(source, destination_dir)

        assert result_path.name == "photo.jpg"
        assert result_path.exists()

    def test_resolves_filename_collision_without_overwriting(self, tmp_path: Path, make_image) -> None:
        source_a = make_image("IMG_0001.jpg", color="red", subdir="camera_a")
        source_b = make_image("IMG_0001.jpg", color="blue", subdir="camera_b")
        destination_dir = tmp_path / "dest"
        copier = SafeFileCopier()

        path_a = copier.copy(source_a, destination_dir)
        path_b = copier.copy(source_b, destination_dir)

        assert path_a != path_b
        assert path_a.name == "IMG_0001.jpg"
        assert path_b.name == "IMG_0001_1.jpg"

        # Both files' contents are genuinely distinct -- neither was overwritten
        from PIL import Image

        assert Image.open(path_a).getpixel((0, 0)) != Image.open(path_b).getpixel((0, 0))

    def test_preserves_modification_time(self, tmp_path: Path, make_image) -> None:
        import os
        import time

        source = make_image("photo.jpg")
        os.utime(source, (time.time() - 10000, time.time() - 10000))
        source_mtime = source.stat().st_mtime

        result_path = SafeFileCopier().copy(source, tmp_path / "dest")

        assert result_path.stat().st_mtime == pytest.approx(source_mtime, abs=1)


class TestPhotoExportService:
    def test_exports_matching_photos_preserving_filenames(
        self,
        export_service: PhotoExportService,
        photo_repo: PhotoRepository,
        face_repo: FaceRepository,
        person_repo: PersonRepository,
        tmp_path: Path,
        make_image,
    ) -> None:
        alice = person_repo.create(display_name="Alice")
        source = make_image("ceremony.jpg", subdir="source")
        photo = photo_repo.create(file_path=str(source))
        face_repo.create(photo_id=photo.id, person_id=alice.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1)

        destination_root = tmp_path / "export"
        destination_root.mkdir()

        result = export_service.export_by_persons([alice.id], destination_root)

        assert result.output_folder == destination_root / "Alice"
        assert result.total_exported == 1
        assert (destination_root / "Alice" / "ceremony.jpg").exists()

    def test_skips_photo_with_missing_source_file_without_aborting(
        self,
        export_service: PhotoExportService,
        photo_repo: PhotoRepository,
        face_repo: FaceRepository,
        person_repo: PersonRepository,
        tmp_path: Path,
        make_image,
    ) -> None:
        alice = person_repo.create(display_name="Alice")
        good_source = make_image("good.jpg", subdir="source")
        good_photo = photo_repo.create(file_path=str(good_source))
        missing_photo = photo_repo.create(file_path=str(tmp_path / "source" / "gone.jpg"))
        face_repo.create(
            photo_id=good_photo.id, person_id=alice.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1
        )
        face_repo.create(
            photo_id=missing_photo.id, person_id=alice.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1
        )

        destination_root = tmp_path / "export"
        destination_root.mkdir()

        result = export_service.export_by_persons([alice.id], destination_root)

        assert result.total_exported == 1
        assert result.total_skipped == 1
        assert "no longer exists" in result.skipped_files[0].reason

    def test_multi_person_export_only_includes_shared_photos(
        self,
        export_service: PhotoExportService,
        photo_repo: PhotoRepository,
        face_repo: FaceRepository,
        person_repo: PersonRepository,
        tmp_path: Path,
        make_image,
    ) -> None:
        alice = person_repo.create(display_name="Alice")
        bob = person_repo.create(display_name="Bob")

        solo_source = make_image("alice_solo.jpg", subdir="source")
        together_source = make_image("together.jpg", subdir="source")
        solo_photo = photo_repo.create(file_path=str(solo_source))
        together_photo = photo_repo.create(file_path=str(together_source))

        face_repo.create(photo_id=solo_photo.id, person_id=alice.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1)
        face_repo.create(
            photo_id=together_photo.id, person_id=alice.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1
        )
        face_repo.create(
            photo_id=together_photo.id, person_id=bob.id, bbox_x=5, bbox_y=5, bbox_width=1, bbox_height=1
        )

        destination_root = tmp_path / "export"
        destination_root.mkdir()

        result = export_service.export_by_persons([alice.id, bob.id], destination_root)

        assert result.output_folder.name == "Alice_Bob"
        assert result.total_exported == 1
        assert (destination_root / "Alice_Bob" / "together.jpg").exists()

    def test_raises_on_nonexistent_destination(
        self, export_service: PhotoExportService, person_repo: PersonRepository, tmp_path: Path
    ) -> None:
        alice = person_repo.create(display_name="Alice")
        with pytest.raises(InvalidDestinationError):
            export_service.export_by_persons([alice.id], tmp_path / "does_not_exist")

    def test_raises_on_destination_that_is_a_file(
        self, export_service: PhotoExportService, person_repo: PersonRepository, tmp_path: Path
    ) -> None:
        alice = person_repo.create(display_name="Alice")
        a_file = tmp_path / "not_a_dir.txt"
        a_file.write_text("hi")
        with pytest.raises(InvalidDestinationError):
            export_service.export_by_persons([alice.id], a_file)

    def test_original_source_file_is_never_modified_or_deleted(
        self,
        export_service: PhotoExportService,
        photo_repo: PhotoRepository,
        face_repo: FaceRepository,
        person_repo: PersonRepository,
        tmp_path: Path,
        make_image,
    ) -> None:
        alice = person_repo.create(display_name="Alice")
        source = make_image("keep_me.jpg", subdir="source")
        original_bytes = source.read_bytes()
        photo = photo_repo.create(file_path=str(source))
        face_repo.create(photo_id=photo.id, person_id=alice.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1)

        destination_root = tmp_path / "export"
        destination_root.mkdir()
        export_service.export_by_persons([alice.id], destination_root)

        assert source.exists()
        assert source.read_bytes() == original_bytes
