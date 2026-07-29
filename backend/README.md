# Wedding Photo Organizer — Backend (Phase 1 + Phase 2)

FastAPI backend: configuration, logging, routing, dependency injection
(Phase 1) plus the SQLite/SQLAlchemy database layer — models,
migrations, repositories (Phase 2). AI pipeline is still Phase 3.

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Create the database

```bash
alembic upgrade head
```

This creates `data/app.db` with the `photos`, `faces`, and `persons`
tables. Safe to re-run — Alembic tracks which migrations have already
been applied in an `alembic_version` table.

## Run

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Verify

- http://127.0.0.1:8000/health → `{"status": "ok", ...}`
- http://127.0.0.1:8000/docs → interactive API docs
- `data/logs/app.log` → confirm the log file was created
- `data/app.db` → confirm the SQLite database file was created

## Making a schema change later

```bash
# 1. Edit/add a model in app/db/models/
# 2. Autogenerate a migration from the model change:
alembic revision --autogenerate -m "describe the change"
# 3. Review the generated file in migrations/versions/ — autogenerate
#    is a strong starting point, not a guarantee; always read it.
# 4. Apply it:
alembic upgrade head
```

## Folder Structure

```
backend/
├── app/
│   ├── main.py             # app factory, startup/shutdown, exception handlers, router mounting
│   ├── core/                 # config, logging, exceptions (no dependency on other layers)
│   ├── api/                   # routers + dependency injection (HTTP boundary)
│   ├── schemas/                 # shared Pydantic request/response models
│   ├── services/                  # business logic (empty — Phase 3 wires this to the DB)
│   ├── db/
│   │   ├── base.py                   # declarative Base + TimestampMixin
│   │   ├── session.py                  # engine, SessionLocal, get_db()
│   │   ├── models/                       # Photo, Face, Person ORM models
│   │   └── repositories/                   # CRUD + query methods per model
│   └── ai/                    # computer vision pipeline (empty — Phase 3)
├── migrations/                  # Alembic migration scripts
├── data/                          # app.db + logs/ land here (gitignored)
├── models/
│   ├── scrfd/det_500m.onnx           # bundled SCRFD face detector weights (~2.5MB)
│   └── arcface/w600k_mbf.onnx          # bundled ArcFace recognition weights (~13.6MB)
├── alembic.ini
├── .env.example
├── .gitignore
└── requirements.txt
```

## Face detection (Phase 4)

```python
from pathlib import Path
from app.ai.face_detection import create_default_face_detection_service

service = create_default_face_detection_service()  # loads the model once
faces = service.detect_in_file(Path("/path/to/photo.jpg"))
for face in faces:
    print(face.confidence, face.bounding_box, face.landmarks)
```

## Face recognition (Phase 5)

```python
import cv2
from app.ai.face_detection import create_default_face_detection_service
from app.ai.face_recognition import create_default_face_recognition_service

detection_service = create_default_face_detection_service()
recognition_service = create_default_face_recognition_service()  # in-memory only

image = cv2.imread("/path/to/photo.jpg")
faces = detection_service.detect_in_array(image)
embeddings = [recognition_service.generate(image, f.landmarks) for f in faces]

# Compare two embeddings (no clustering — just a pairwise check)
similarity = embeddings[0].cosine_similarity(embeddings[1])
```

To persist embeddings into the Phase 2 database, pass a live session:

```python
from app.db.session import SessionLocal

db = SessionLocal()
recognition_service = create_default_face_recognition_service(db_session=db)
recognition_service.generate_and_store(face_id=42, image=image, landmarks=faces[0].landmarks)
```

## Face clustering (Phase 6)

```python
from app.ai.clustering import create_default_face_clustering_service
from app.ai.clustering.models import EmbeddingRecord

records = [EmbeddingRecord(identifier=face_id, embedding=emb) for face_id, emb in ...]

clustering_service = create_default_face_clustering_service()
result = clustering_service.cluster(records)

for person in result.person_clusters:
    print(person.person_label, "->", person.member_identifiers)
print("Unknown faces:", result.unknown_face_identifiers)
```

Tune `CLUSTERING_EPS` / `CLUSTERING_MIN_SAMPLES` in `.env` to control how
strict grouping is — see DBSCANFaceClusterer's docstring for guidance.

## Search API (Phase 7)

The first real HTTP endpoints. Requires the database to be migrated
(`alembic upgrade head`) and running (`uvicorn app.main:app`).

```
GET /search/photos?person_ids=1
    -> every photo person 1 appears in

GET /search/photos?person_ids=1&person_ids=2
    -> only photos where BOTH person 1 AND person 2 appear together
```

Response:

```json
{
  "persons": [{"id": 1, "display_name": "Alice"}],
  "photos": [{"id": 3, "file_path": "/wedding/photo3.jpg", "taken_at": null, "width": null, "height": null}],
  "total_photos": 1
}
```

Searching for a person id that doesn't exist returns `404` with the
standard error envelope; omitting `person_ids` entirely returns `422`.

## Export API (Phase 8)

```
POST /export/photos
{
  "person_ids": [1],
  "destination_root": "/Users/me/Desktop/wedding_export"
}
```

Creates a person-named subfolder inside `destination_root` (e.g.
`.../wedding_export/Alice/`, or `.../Alice_Bob/` for a multi-person
search) and copies every matching photo into it, preserving original
filenames. A filename collision (two source photos sharing a name)
is resolved by appending `_1`, `_2`, ... — never by overwriting.
Originals are always copied, never moved or modified.

Response:

```json
{
  "output_folder": "/Users/me/Desktop/wedding_export/Alice",
  "exported_files": [{"source_path": "...", "destination_path": "..."}],
  "skipped_files": [{"source_path": "...", "reason": "Source file no longer exists on disk"}],
  "total_exported": 3,
  "total_skipped": 1
}
```

An unwritable/nonexistent `destination_root` returns `422`; an unknown
`person_ids` entry returns `404` — same error envelope as search.

Both model weight files are bundled locally under `models/` — nothing
is downloaded at runtime. As with the SCRFD file, these are binary
weights better tracked with Git LFS in a real repo than committed
directly.
