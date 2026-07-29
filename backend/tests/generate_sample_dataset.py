"""
Sample dataset generator.

Produces two things a developer or QA tester actually needs when
poking at this app by hand (not through pytest):

1. A folder of real, valid, synthetic "wedding photos" on disk —
   nested subfolders, mixed formats, an exact-duplicate, a corrupted
   file, and an unsupported file — matching every case the scanning
   module (Phase 3) is designed to handle.
2. A fully seeded SQLite database (Photo/Face/Person rows,
   pre-clustered "people") consistent with that photo folder, so the
   search and export APIs (Phase 7/8) have something realistic to
   query immediately, without needing a real face-detection run first.

Usage:
    python -m tests.generate_sample_dataset [--output-dir DIR]

This is intentionally a standalone script, not a pytest fixture — it's
meant to be run manually to produce a dataset a human (or the frontend,
pointed at this backend) can explore interactively.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Face, Person, Photo  # noqa: F401  (registers models on Base.metadata)
from app.db.repositories import FaceRepository, PersonRepository, PhotoRepository

# A small, readable color palette so generated photos are visually
# distinguishable from each other in a file browser / image viewer.
_COLORS = [
    "indianred", "steelblue", "goldenrod", "seagreen", "orchid",
    "sienna", "slategray", "darkkhaki", "teal", "salmon",
]


def _make_photo_library(output_dir: Path) -> dict[str, Path]:
    """
    Build a realistic nested folder of photo files, covering every
    scanning-module edge case in one pass.

    Returns a dict of notable paths (by label) for the caller to wire
    into the seeded database.
    """
    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "ceremony").mkdir(parents=True)
    (output_dir / "reception").mkdir(parents=True)
    (output_dir / "getting_ready").mkdir(parents=True)

    paths: dict[str, Path] = {}

    def photo(relative: str, size: tuple[int, int] = (800, 600), color: str | None = None) -> Path:
        path = output_dir / relative
        Image.new("RGB", size, color=color or _COLORS[len(paths) % len(_COLORS)]).save(path)
        paths[relative] = path
        return path

    # Normal, everyday photos across three "events"
    photo("getting_ready/bride_prep_01.jpg")
    photo("getting_ready/bride_prep_02.JPG")  # uppercase extension, should still count
    photo("ceremony/vows_01.jpg")
    photo("ceremony/vows_02.png")
    photo("ceremony/rings.jpeg")
    photo("reception/first_dance.jpg")
    photo("reception/cake_cutting.jpg")
    photo("reception/group_photo.jpg", size=(1600, 1200))

    # An exact duplicate (same bytes) dropped into a second folder — the
    # kind of thing that happens when two guests' phones both upload
    # the same shared photo into the import folder
    shutil.copy(paths["reception/first_dance.jpg"], output_dir / "reception" / "first_dance_copy.jpg")

    # A file with a supported extension but corrupted contents
    (output_dir / "reception" / "corrupted.jpg").write_bytes(b"not actually a jpeg")

    # A file that should be silently ignored
    (output_dir / "reception" / "notes.txt").write_text("remember to thank the caterer")

    return paths


def _seed_database(db_path: Path, photo_paths: dict[str, Path]) -> None:
    """
    Create a fresh SQLite database at db_path and populate it with
    Person/Photo/Face rows consistent with the generated photo library,
    simulating what Phases 3-6 (scanning, detection, recognition,
    clustering) would have produced from a real run.
    """
    if db_path.exists():
        db_path.unlink()

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    photo_repo = PhotoRepository(db)
    face_repo = FaceRepository(db)
    person_repo = PersonRepository(db)

    # Three named, confirmed people (the common case) + one
    # unconfirmed auto-cluster (simulating Phase 6 output awaiting
    # human review) — covers both states the People shelf needs to render.
    bride = person_repo.create(display_name="Bride", is_confirmed=True)
    groom = person_repo.create(display_name="Groom", is_confirmed=True)
    mother = person_repo.create(display_name="Mother of the Bride", is_confirmed=True)
    unconfirmed = person_repo.create(display_name=None, is_confirmed=False)

    def add_photo_with_people(relative_path: str, person_ids: list[int]) -> None:
        photo = photo_repo.create(file_path=str(photo_paths[relative_path]))
        for index, person_id in enumerate(person_ids):
            face_repo.create(
                photo_id=photo.id,
                person_id=person_id,
                bbox_x=10 + index * 60,
                bbox_y=10,
                bbox_width=50,
                bbox_height=50,
                confidence_score=0.9,
            )

    add_photo_with_people("getting_ready/bride_prep_01.jpg", [bride.id])
    add_photo_with_people("getting_ready/bride_prep_02.JPG", [bride.id, mother.id])
    add_photo_with_people("ceremony/vows_01.jpg", [bride.id, groom.id])
    add_photo_with_people("ceremony/vows_02.png", [bride.id, groom.id])
    add_photo_with_people("ceremony/rings.jpeg", [])  # no faces (a detail shot)
    add_photo_with_people("reception/first_dance.jpg", [bride.id, groom.id])
    add_photo_with_people("reception/cake_cutting.jpg", [bride.id, groom.id, mother.id])
    add_photo_with_people("reception/group_photo.jpg", [bride.id, groom.id, mother.id, unconfirmed.id])

    db.commit()
    db.close()


def generate(output_dir: Path) -> None:
    photos_dir = output_dir / "photos"
    db_path = output_dir / "sample.db"

    photo_paths = _make_photo_library(photos_dir)
    _seed_database(db_path, photo_paths)

    print(f"Sample photo library: {photos_dir}")
    print(f"Sample database:      {db_path}")
    print()
    print("To use this database with the running app:")
    print(f'  cp "{db_path}" data/app.db')
    print()
    print("Seeded people: Bride, Groom, 'Mother of the Bride', and one unconfirmed cluster.")
    print("Try: GET /search/photos?person_ids=1  (Bride)")
    print("     GET /search/photos?person_ids=1&person_ids=2  (Bride + Groom)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "sample_data",
        help="Where to write the sample photo library and database (default: tests/sample_data)",
    )
    args = parser.parse_args()
    generate(args.output_dir)
