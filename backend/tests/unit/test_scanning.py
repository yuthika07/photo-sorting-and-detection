"""
Tests for app/scanning/ (Phase 3).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.scanning import create_default_image_scanner
from app.scanning.duplicate_path_detector import InMemoryDuplicatePathDetector
from app.scanning.exceptions import ImageMetadataExtractionError, InvalidScanRootError
from app.scanning.folder_scanner import RecursiveFolderScanner
from app.scanning.format_validator import ExtensionImageFormatValidator
from app.scanning.metadata_extractor import PillowMetadataExtractor


class TestExtensionImageFormatValidator:
    def test_accepts_supported_extensions(self, tmp_path: Path) -> None:
        validator = ExtensionImageFormatValidator()
        for name in ["a.jpg", "b.jpeg", "c.png", "d.JPG", "e.PNG"]:
            assert validator.is_supported(tmp_path / name) is True

    def test_rejects_unsupported_extensions(self, tmp_path: Path) -> None:
        validator = ExtensionImageFormatValidator()
        for name in ["notes.txt", "video.mp4", "archive.zip", "noext"]:
            assert validator.is_supported(tmp_path / name) is False

    def test_custom_extension_set(self, tmp_path: Path) -> None:
        # Open/Closed: new formats supported via construction, no code change
        validator = ExtensionImageFormatValidator(frozenset({".heic"}))
        assert validator.is_supported(tmp_path / "photo.heic") is True
        assert validator.is_supported(tmp_path / "photo.jpg") is False


class TestInMemoryDuplicatePathDetector:
    def test_first_occurrence_is_not_duplicate(self, tmp_path: Path) -> None:
        detector = InMemoryDuplicatePathDetector()
        path = tmp_path / "a.jpg"
        assert detector.check_and_mark(path) is False

    def test_second_occurrence_is_duplicate(self, tmp_path: Path) -> None:
        detector = InMemoryDuplicatePathDetector()
        path = tmp_path / "a.jpg"
        detector.check_and_mark(path)
        assert detector.check_and_mark(path) is True

    def test_symlink_to_same_file_is_detected_as_duplicate(self, tmp_path: Path, make_image) -> None:
        real_file = make_image("real.jpg")
        symlink_path = tmp_path / "link.jpg"
        os.symlink(real_file, symlink_path)

        detector = InMemoryDuplicatePathDetector()
        assert detector.check_and_mark(real_file) is False
        assert detector.check_and_mark(symlink_path) is True  # resolves to the same file


class TestRecursiveFolderScanner:
    def test_walks_nested_directories(self, tmp_path: Path, make_image) -> None:
        make_image("a.jpg")
        make_image("b.jpg", subdir="nested")
        make_image("c.jpg", subdir="nested/deeper")

        scanner = RecursiveFolderScanner()
        found = {p.name for p in scanner.walk(tmp_path)}
        assert found == {"a.jpg", "b.jpg", "c.jpg"}

    def test_raises_on_nonexistent_root(self, tmp_path: Path) -> None:
        scanner = RecursiveFolderScanner()
        with pytest.raises(InvalidScanRootError):
            list(scanner.walk(tmp_path / "does_not_exist"))

    def test_raises_when_root_is_a_file_not_a_directory(self, tmp_path: Path, make_image) -> None:
        file_path = make_image("a.jpg")
        scanner = RecursiveFolderScanner()
        with pytest.raises(InvalidScanRootError):
            list(scanner.walk(file_path))


class TestPillowMetadataExtractor:
    def test_extracts_correct_dimensions_and_filename(self, make_image) -> None:
        path = make_image("photo.jpg", size=(200, 150))
        extractor = PillowMetadataExtractor()

        metadata = extractor.extract(path)

        assert metadata.width == 200
        assert metadata.height == 150
        assert metadata.filename == "photo.jpg"
        assert metadata.file_size_bytes > 0

    def test_raises_on_corrupted_file(self, tmp_path: Path) -> None:
        corrupt = tmp_path / "corrupt.jpg"
        corrupt.write_bytes(b"this is not a real jpeg")

        extractor = PillowMetadataExtractor()
        with pytest.raises(ImageMetadataExtractionError):
            extractor.extract(corrupt)


class TestImageScannerOrchestrator:
    """Integration-style tests for the full ImageScanner pipeline."""

    def test_finds_all_supported_images_in_nested_folders(self, tmp_path: Path, make_image) -> None:
        make_image("photo1.jpg", subdir="ceremony")
        make_image("photo2.JPG", subdir="ceremony")
        make_image("photo3.png", subdir="reception")

        report = create_default_image_scanner().scan(tmp_path)

        assert report.total_images_found == 3
        assert report.total_files_skipped == 0

    def test_ignores_unsupported_files_without_erroring(self, tmp_path: Path, make_image) -> None:
        make_image("photo.jpg")
        (tmp_path / "notes.txt").write_text("not an image")

        report = create_default_image_scanner().scan(tmp_path)

        assert report.total_images_found == 1
        assert len(report.unsupported_paths) == 1

    def test_isolates_a_single_corrupted_file_without_aborting_the_scan(
        self, tmp_path: Path, make_image
    ) -> None:
        make_image("good1.jpg")
        make_image("good2.jpg")
        (tmp_path / "bad.jpg").write_bytes(b"garbage")

        report = create_default_image_scanner().scan(tmp_path)

        assert report.total_images_found == 2
        assert len(report.failed_paths) == 1

    def test_detects_duplicate_path_via_symlink(self, tmp_path: Path, make_image) -> None:
        real = make_image("photo.jpg")
        os.symlink(real, tmp_path / "photo_link.jpg")

        report = create_default_image_scanner().scan(tmp_path)

        assert report.total_images_found == 1
        assert len(report.duplicate_paths) == 1

    def test_empty_folder_returns_empty_report_not_an_error(self, tmp_path: Path) -> None:
        report = create_default_image_scanner().scan(tmp_path)

        assert report.total_images_found == 0
        assert report.total_files_skipped == 0

    def test_raises_on_invalid_root(self, tmp_path: Path) -> None:
        with pytest.raises(InvalidScanRootError):
            create_default_image_scanner().scan(tmp_path / "nope")
