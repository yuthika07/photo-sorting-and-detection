# Wedding Photo Organizer — Test Plan

**Status at time of writing:** 114 backend tests passing (92% line
coverage), 37 frontend tests passing. All numbers below are from
actual runs of the suite, not estimates.

---

## 1. Testing strategy — the reasoning

### 1.1 Test pyramid, applied to an offline, AI-heavy desktop app

This app has an unusual shape compared to a typical CRUD web app: it
has a real database layer, a real HTTP API, AND a chain of ML models
(SCRFD, ArcFace) that are expensive to load and slow to run. A
one-size-fits-all testing approach doesn't fit that shape well, so the
suite is deliberately layered:

```
        Fewer, slower
   E2E / manual QA          <- sample dataset + real server, by hand
   API tests (TestClient)    <- real HTTP, real (in-memory) DB, fake nothing
   Service/unit tests          <- real DB, FAKE ML models (see 1.2)
   Pure logic tests               <- no DB, no I/O (clustering math, models)
        More, faster
```

Every layer below "API tests" runs in milliseconds and needs nothing
external. That's what keeps the suite fast enough to run on every save
during development, while still having true end-to-end coverage at the
top.

### 1.2 The one deliberate trade-off: fakes for ML models, real models for a marked-`slow` subset

Loading a real ONNX model (SCRFD ~2.5MB, ArcFace ~13.6MB) and running
inference takes real, human-noticeable time -- multiplied across dozens
of test cases, that's the difference between a test suite a developer
actually runs before every commit and one they start avoiding.

So: every test that exercises **orchestration logic** (does
`FaceDetectionService.detect_in_file` correctly call the loader, then
the detector, and propagate errors correctly?) uses a hand-written
**fake** implementing the same interface (`FakeFaceDetector`,
`FakeEmbedder`) -- see `tests/unit/test_face_detection.py` and
`test_face_recognition.py`. This is possible specifically *because*
Phases 4-6 were built with SOLID's Dependency Inversion in mind: every
consumer depends on an abstract interface, never a concrete class, so
swapping in a test double requires no production code changes at all.

A small number of tests, marked `@pytest.mark.slow`, load the
**actual bundled model files** and run **real inference** -- these
catch the class of bug a fake can never catch (a wrong file path, a
real preprocessing mismatch, the confidence filter not actually wired
to the real model's real output shape). Run the fast suite during
normal development:

```bash
pytest -m "not slow"
```

Run everything (recommended before a release, and in CI) with:

```bash
pytest
```

### 1.3 Real database, every time -- never mocked

The DB layer is never faked. Every test that touches persistence uses
a genuinely fresh SQLite database (in-memory, via `StaticPool` so every
connection in the test shares the same instance -- see
`tests/conftest.py`), created directly from the real ORM models'
metadata. Mocking the ORM would mean testing that mocks behave like
mocks, not that cascade deletes, unique constraints, and query
semantics behave the way the schema actually promises they do. This is
exactly why `test_db_repositories.py::TestRelationshipsAndCascades`
exists -- a mock can't accidentally reveal that `ondelete="CASCADE"`
isn't actually enforced; only a real database can.

### 1.4 Real files, every time -- never faked, for scanning and export

Both `app/scanning/` and `app/services/export/` are fundamentally
about file I/O. A test using fake bytes or a mocked filesystem would
validate nothing real about them. Every test in `test_scanning.py` and
`test_export_service.py` uses `tmp_path` (pytest's built-in temp
directory fixture) and writes genuinely valid image files via Pillow --
including a genuinely corrupted file, a genuine symlink, and two
genuinely distinct source files that happen to share a filename, to
prove the collision handling doesn't just avoid a crash but actually
preserves both images' real content (verified pixel-by-pixel in
`test_resolves_filename_collision_without_overwriting`).

### 1.5 API tests exercise the real HTTP stack, not the service layer directly

`tests/api/` uses FastAPI's `TestClient` against the real `app` object
from `app.main`, with only the database swapped for a test-isolated
one (via `app.dependency_overrides`). This is what actually proves
request parsing, dependency injection, router wiring, and -- critically
-- the global exception handlers registered in Phase 1 all work
together. `test_error_handling.py` is the sharpest example: it proves
that a genuine, unexpected bug (a monkeypatched `RuntimeError`) comes
back as a safe, generic 500 rather than a stack trace leaking to the
client or the server crashing -- something no unit test of the service
layer alone could ever verify, since that translation only happens at
the ASGI/middleware layer.

### 1.6 Frontend: fakes at the network boundary, real everything else

`lib/api/*.test.ts` mock only `apiClient`'s `get`/`post` methods --
never the mapping logic around them -- so the snake_case -> camelCase
translation and the empty-input guard are tested for real.
`useAppStore.test.ts` mocks the three API modules the store calls, but
runs the actual Zustand store, actual selection/search/rename/export
logic, unmocked -- proving the "instant filtering" behavior (selecting
a person re-triggers a real search call with the real accumulated
list) genuinely works, not just that a mock was configured correctly.
Component tests (`PersonCard`, `PersonChip`, `Button`) use real
rendering and real user-event clicks via Testing Library -- never
shallow rendering or snapshot testing, which tend to test that a
component renders the same "-ish" markup, not that it *behaves*
correctly (e.g. that clicking Rename does NOT also trigger selection --
a real regression risk given the event bubbling involved, verified
explicitly).

---

## 2. What's covered, by layer

### 2.1 Backend -- unit-level (`backend/tests/unit/`)

| File | Covers |
|---|---|
| `test_core.py` | Settings defaults, `.env` parsing, `get_settings()` caching, `AppException` hierarchy |
| `test_logging.py` | Log file/directory creation, log level applied, no duplicate handlers on reconfigure |
| `test_scanning.py` | Format validation, duplicate-path detection (incl. symlinks), recursive folder walking, real Pillow metadata extraction, corrupted-file isolation, full `ImageScanner` orchestration |
| `test_db_repositories.py` | CRUD for all three repositories, relationship navigation both directions, **cascade delete** (Photo->Face) and **set-null** (Person->Face) verified against a real SQLite engine |
| `test_face_detection.py` | `OpenCVImageLoader` (valid/missing/corrupted), `FaceDetectionService` orchestration via fake, **+ slow:** real SCRFD model load failure, zero-face case, confidence/bbox structure |
| `test_face_recognition.py` | `FaceEmbedding` validation/immutability/cosine similarity math, serializer round-trip + exact byte size, `SQLiteFaceEmbeddingStore` save/load/missing-face, service orchestration via fake, **+ slow:** real ArcFace model load failure, real 512-d normalized output, missing-landmarks error |
| `test_clustering.py` | Empty input, mismatched model/dimension guards, correct grouping of similar embeddings, **correct noise handling for single-appearance faces**, deterministic "Person N" ordering by cluster size, order-independence |
| `test_export_service.py` | Folder naming (single/multi/unnamed/sanitization/order-independence), **real file collision resolution with pixel-verified distinct content**, modification-time preservation, per-file missing-source isolation, multi-person AND export, invalid-destination guards, **originals never modified** |
| `test_search_service.py` | Single/double/triple-person AND search against a realistic 3-person/5-photo dataset, resolved person objects returned, unknown-id / partial-unknown-id error detail, empty-result case, duplicate-id-in-request deduplication |

### 2.2 Backend -- API-level (`backend/tests/api/`)

| File | Covers |
|---|---|
| `test_health.py` | Basic liveness contract |
| `test_search_api.py` | Real HTTP GET, repeated-query-param parsing, AND semantics over HTTP, 422 on missing param, 404 + standard envelope on unknown person |
| `test_export_api.py` | Real HTTP POST with real temp files, folder creation over HTTP, 422 on bad destination, 404 on unknown person, 422 on empty list, skipped-file reporting over HTTP |
| `test_error_handling.py` | An unexpected, unhandled exception is converted to a safe generic 500 -- **and the real bug's message is confirmed absent from the response** |

### 2.3 Frontend (`frontend/`)

| File | Covers |
|---|---|
| `lib/api/__tests__/client.test.ts` | Error-envelope extraction, network-failure mapping, timeout mapping, unknown-shape fallback, non-Error/non-axios inputs |
| `lib/api/__tests__/search.test.ts` | Empty-input guard, param serialization, snake->camel mapping, error propagation |
| `lib/api/__tests__/export.test.ts` | Same, for export -- including skipped-file reason mapping |
| `lib/store/__tests__/useAppStore.test.ts` | People loading (success/error), **instant re-search on every selection change**, AND-list accumulation, removal, clear, rename (success + rethrow-on-failure + isolated patching of only the renamed person), export (idle-guard, success, error, dismiss) |
| `components/__tests__/Button.test.tsx` | Render, click, disabled-blocks-click |
| `components/__tests__/PersonChip.test.tsx` | Render, remove callback |
| `components/__tests__/PersonCard.test.tsx` | Name/count rendering incl. singular "1 photo", selection toggle, `aria-pressed` reflects selection, **Rename/Export do not also trigger selection**, unnamed fallback |

---

## 3. Edge case matrix

Every row below is an actual, automated test -- not a hypothetical.

| Category | Edge case | Test |
|---|---|---|
| Scanning | Unsupported file extension | `test_ignores_unsupported_files_without_erroring` |
| Scanning | Corrupted file with a valid-looking extension | `test_isolates_a_single_corrupted_file_without_aborting_the_scan` |
| Scanning | Duplicate path via symlink | `test_detects_duplicate_path_via_symlink` |
| Scanning | Empty folder | `test_empty_folder_returns_empty_report_not_an_error` |
| Scanning | Nonexistent / non-directory root | `test_raises_on_invalid_root`, `test_raises_when_root_is_a_file_not_a_directory` |
| Detection | Zero faces in an image | `test_zero_faces_is_a_normal_result_not_an_error`, blank-image real-model test |
| Detection | Missing/corrupted image file | `TestOpenCVImageLoader::test_raises_on_missing_file` / `..._corrupted_file` |
| Detection | Missing model file | `test_raises_model_load_error_for_missing_file` |
| Recognition | Missing landmarks (unaligned face) | `test_raises_invalid_landmarks_error_when_none` |
| Recognition | Degenerate/mismatched embeddings compared | `test_cosine_similarity_raises_on_model_mismatch` / `..._dimension_mismatch` |
| Recognition | Attempted mutation of a "stored" embedding | `test_vector_is_immutable` |
| Clustering | Empty embedding set | `test_raises_on_empty_input` |
| Clustering | Mismatched models/dimensions in one batch | `test_raises_on_mismatched_models` / `..._dimensions` |
| Clustering | Every face appears exactly once (min_samples never satisfied) | `test_dissimilar_single_appearances_become_unknown` |
| Clustering | Mixed real clusters + a lone stranger in the same batch | `test_mixed_scenario_clusters_and_unknowns_together` |
| Database | Deleting a Photo | cascades to Face (`test_deleting_photo_cascades_to_faces`) |
| Database | Deleting a Person | un-links but does not delete Face (`test_deleting_person_unlinks_but_does_not_delete_faces`) |
| Database | Looking up a nonexistent row | every repo's `test_get_missing_returns_none`-style test |
| Search | Unknown person id | `test_search_with_unknown_person_id_raises_not_found` |
| Search | One known + one unknown id | `test_partial_unknown_ids_reports_only_the_missing_one` |
| Search | Person exists but has zero photos | `test_search_for_person_with_no_photos_returns_empty` |
| Search | Same id repeated in one request | `test_duplicate_person_ids_in_request_are_deduplicated` |
| Export | Two different source files sharing a filename | `test_resolves_filename_collision_without_overwriting` (pixel-verified) |
| Export | A DB row pointing at a file that no longer exists | `test_skips_photo_with_missing_source_file_without_aborting` |
| Export | Destination folder doesn't exist / is a file | `test_raises_on_nonexistent_destination` / `..._that_is_a_file` |
| Export | Multi-person export only includes shared photos | `test_multi_person_export_only_includes_shared_photos` |
| Export | Originals must never be modified | `test_original_source_file_is_never_modified_or_deleted` |
| API | Missing required query param | `test_search_missing_person_ids_param_returns_422` |
| API | Empty required list in POST body | `test_export_empty_person_ids_returns_422` |
| API | A genuine unhandled bug | `test_unexpected_error_returns_generic_500_not_a_crash` |
| Frontend | Network failure / timeout | `client.test.ts` |
| Frontend | Empty selection prevents an API call | `search.test.ts`, `export.test.ts`, `useAppStore.test.ts::does nothing when nothing is selected` |
| Frontend | Rename fails -- dialog must stay open | `renamePerson::rethrows on failure` |
| Frontend | Clicking a card sub-button must not also select the card | `PersonCard.test.tsx::event isolation` |

---

## 4. Sample datasets

### 4.1 Generated dataset (`backend/tests/generate_sample_dataset.py`)

Run manually -- this is NOT part of the pytest suite, it's for a human
(or the frontend, pointed at a running backend) to explore:

```bash
cd backend
python -m tests.generate_sample_dataset --output-dir tests/sample_data
cp tests/sample_data/sample.db data/app.db
uvicorn app.main:app --reload
```

It produces:

- **A real photo folder** (`sample_data/photos/`) with three
  subfolders (`getting_ready/`, `ceremony/`, `reception/`), 8 valid
  images across `.jpg`/`.JPG`/`.png`/`.jpeg`, one exact byte-for-byte
  duplicate, one corrupted file, and one unsupported `.txt` file -- the
  same shape of "messy real folder" the scanning module (Phase 3) is
  designed to handle.
- **A fully seeded SQLite database** with 4 people (`Bride`, `Groom`,
  `Mother of the Bride` -- all confirmed -- plus one unconfirmed
  auto-cluster) and 16 face assignments across the 8 photos, so
  `/search/photos` and `/export/photos` have something realistic to
  return immediately.

Verified live while building this test suite -- querying the generated
data reproduces the exact three examples from the original brief:

```
GET /search/photos?person_ids=1               -> 7 photos  (Bride)
GET /search/photos?person_ids=1&person_ids=2   -> 5 photos  (Bride + Groom)
GET /search/photos?person_ids=1&person_ids=3   -> 3 photos  (Bride + Mother)
```

### 4.2 In-test synthetic datasets

Beyond the standalone generator, the suite builds smaller, purpose-fit
datasets inline, per test, via fixtures:

- `make_image()` (`conftest.py`) -- writes a real, valid, arbitrarily
  colored/sized image to a temp directory; used everywhere the
  scanning/detection/export modules need a genuine file to operate on.
- `seeded_wedding` (`test_search_service.py`) -- the canonical
  "Alice/Bob/Carol across 5 photos with every AND-combination
  represented" dataset, reused conceptually by the API-level search
  tests.
- Orthogonal one-hot embedding vectors (`test_clustering.py`) --
  synthetic low-dimensional embeddings constructed to have EXACTLY
  known cosine distances between "people," so clustering assertions
  are deterministic rather than dependent on chance separation between
  random vectors (an earlier version of this test using independent
  random base vectors was flaky for exactly this reason -- a real bug
  caught by running the suite repeatedly, not a hypothetical).

---

## 5. Running everything

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
pytest                          # full suite, incl. real-model tests
pytest -m "not slow"            # fast subset only
pytest --cov=app --cov-report=term-missing   # with coverage

# Frontend
cd frontend
npm install
npm run test                    # vitest run
npm run build                   # production build + full TS check
```

## 6. Known gaps (documented, not hidden)

- The backend's `GET /persons` / `PATCH /persons/{id}` endpoints don't
  exist yet (see `frontend/lib/api/persons.ts`), so there is no
  automated test for them on either side -- nothing to test until they
  exist. The frontend store/component tests cover the client-side
  behavior against a mocked version of that contract instead.
- E2E browser testing (a real Next.js app driving a real running
  backend through a real browser) isn't automated in this pass -- the
  closest equivalent exercised here is the manual verification in
  Section 4.1, run for real against the actual server during this
  test-writing session.
- `npm run lint` has a known tooling-version incompatibility unrelated
  to application code (see `frontend/README.md`); `npm run build`'s
  full TypeScript check is the authoritative correctness gate for now.
