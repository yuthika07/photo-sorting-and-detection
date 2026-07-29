/**
 * Shared domain types.
 *
 * `PersonSummary` and `Photo`/`SearchPhotosResult`/`ExportResult` mirror
 * the backend's ACTUAL response shapes exactly:
 *   - PersonSummary / PhotoSummary / SearchPhotosResponse -- app/schemas/search.py
 *   - ExportPhotosResponse -- app/schemas/export.py
 *
 * `Person` is deliberately a superset (photoCount, thumbnailUrl,
 * isConfirmed) that the People shelf needs to render cards, but that
 * /search/photos's PersonSummary does not provide. The backend has no
 * "list all people" endpoint yet (only /search/photos and
 * /export/photos exist so far -- see backend/README.md). lib/api/persons.ts
 * is written against the endpoint this UI expects to exist
 * (`GET /persons`) and documents that assumption explicitly -- wiring
 * it to a real backend route is future backend work, not part of this
 * frontend-only phase.
 */

export interface PersonSummary {
  id: number;
  displayName: string | null;
}

export interface Person extends PersonSummary {
  photoCount: number;
  thumbnailUrl: string | null;
  isConfirmed: boolean;
}

export interface Photo {
  id: number;
  filePath: string;
  takenAt: string | null;
  width: number | null;
  height: number | null;
  /** Not yet served by the backend; falls back to a placeholder -- see PhotoCard. */
  thumbnailUrl?: string | null;
}

export interface SearchPhotosResult {
  persons: PersonSummary[];
  photos: Photo[];
  totalPhotos: number;
}

export interface ExportedFile {
  sourcePath: string;
  destinationPath: string;
}

export interface SkippedFile {
  sourcePath: string;
  reason: string;
}

export interface ExportResult {
  outputFolder: string;
  exportedFiles: ExportedFile[];
  skippedFiles: SkippedFile[];
  totalExported: number;
  totalSkipped: number;
}

/** The standard error envelope every backend AppException produces. */
export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
