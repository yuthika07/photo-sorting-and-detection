"""
Tests for POST /export/photos (Phase 8), over real HTTP with real
temporary files on disk.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.db.repositories import FaceRepository, PersonRepository, PhotoRepository


class TestExportPhotosEndpoint:
    def test_export_single_person_creates_named_folder_and_copies_file(
        self,
        client: TestClient,
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

        response = client.post(
            "/export/photos",
            json={"person_ids": [alice.id], "destination_root": str(destination_root)},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total_exported"] == 1
        assert body["output_folder"] == str(destination_root / "Alice")
        assert (destination_root / "Alice" / "ceremony.jpg").exists()

    def test_export_to_nonexistent_destination_returns_422(
        self, client: TestClient, person_repo: PersonRepository, tmp_path: Path
    ) -> None:
        alice = person_repo.create(display_name="Alice")

        response = client.post(
            "/export/photos",
            json={"person_ids": [alice.id], "destination_root": str(tmp_path / "nope")},
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_FAILED"

    def test_export_unknown_person_returns_404(self, client: TestClient, tmp_path: Path) -> None:
        response = client.post(
            "/export/photos", json={"person_ids": [999], "destination_root": str(tmp_path)}
        )
        assert response.status_code == 404

    def test_export_empty_person_ids_returns_422(self, client: TestClient, tmp_path: Path) -> None:
        response = client.post(
            "/export/photos", json={"person_ids": [], "destination_root": str(tmp_path)}
        )
        assert response.status_code == 422

    def test_export_reports_skipped_missing_source_files(
        self,
        client: TestClient,
        photo_repo: PhotoRepository,
        face_repo: FaceRepository,
        person_repo: PersonRepository,
        tmp_path: Path,
    ) -> None:
        alice = person_repo.create(display_name="Alice")
        missing_photo = photo_repo.create(file_path=str(tmp_path / "gone.jpg"))
        face_repo.create(
            photo_id=missing_photo.id, person_id=alice.id, bbox_x=0, bbox_y=0, bbox_width=1, bbox_height=1
        )
        destination_root = tmp_path / "export"
        destination_root.mkdir()

        response = client.post(
            "/export/photos",
            json={"person_ids": [alice.id], "destination_root": str(destination_root)},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total_exported"] == 0
        assert body["total_skipped"] == 1
