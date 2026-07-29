# Wedding Photo Organizer

An offline desktop application for organizing wedding photos by the
people in them: detect faces, cluster them into people, search by any
combination of people ("Bride", "Bride + Groom", "Bride + Mother"),
and export matching photos into named folders — all running locally,
with no cloud calls.

```
wedding-photo-organizer/
├── backend/          FastAPI + SQLite + SCRFD/ArcFace/DBSCAN pipeline
├── frontend/         Next.js + TypeScript + Tailwind (skeuomorphic desktop UI)
└── TEST_PLAN.md      Full testing strategy, edge case matrix, sample datasets
```

## Quick start

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend** (in a second terminal):
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

**Try it with real data** instead of an empty database:
```bash
cd backend
python -m tests.generate_sample_dataset --output-dir tests/sample_data
cp tests/sample_data/sample.db data/app.db
```

Then visit `http://localhost:3000` (frontend needs a running backend
to load anything).

## Running the tests

```bash
# Backend — 114 tests, 92% coverage
cd backend && pip install -r requirements-dev.txt && pytest

# Frontend — 37 tests
cd frontend && npm run test
```

See `TEST_PLAN.md` for the full strategy, the edge-case matrix, and
what's covered where.

## What's built (by phase)

| Phase | What | Where |
|---|---|---|
| 1 | FastAPI skeleton: config, logging, routing, DI, clean architecture | `backend/app/{core,api}/` |
| 2 | SQLite + SQLAlchemy: Photo/Face/Person models, Alembic, repositories | `backend/app/db/` |
| 3 | Recursive photo scanning: format validation, dedup, metadata | `backend/app/scanning/` |
| 4 | Face detection: SCRFD, bounding boxes + landmarks | `backend/app/ai/face_detection/` |
| 5 | Face recognition: ArcFace, 512-d embeddings, storage | `backend/app/ai/face_recognition/` |
| 6 | Face clustering: DBSCAN, "Person N" + unknown handling | `backend/app/ai/clustering/` |
| 7 | Search API: photos containing one or more people (AND) | `backend/app/api/routers/search.py` |
| 8 | Export API: copy matching photos into named folders | `backend/app/services/export/` |
| 9 | Frontend: skeuomorphic desktop UI, Zustand, Axios API layer | `frontend/` |
| 10 | Comprehensive test suite + sample datasets | `backend/tests/`, `frontend/**/__tests__/` |

Each backend module was built with SOLID principles (abstract
interfaces + dependency injection throughout), verified with real
model inference and real files on disk during development — not just
written and assumed to work. See each module's own docstrings and
`backend/README.md` / `frontend/README.md` for deeper detail.

## Known, documented gaps

- `GET /persons` and `PATCH /persons/{id}` (list/rename people) are
  assumed by the frontend but not yet built on the backend — see
  `frontend/lib/api/persons.ts` for the exact contract expected.
- No AI worker/job-queue wiring yet connecting scanning → detection →
  recognition → clustering into one automatic pipeline run; each stage
  is complete and tested individually, ready to be orchestrated.
- No packaged desktop shell (Tauri/Electron) yet — both apps currently
  run as a normal local dev server + API pair.
