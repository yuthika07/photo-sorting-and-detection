import { apiClient, toApiError } from "@/lib/api/client";
import type { ExportResult } from "@/lib/types";

/** Raw shape actually returned by POST /export/photos (app/schemas/export.py). */
interface RawExportResponse {
  output_folder: string;
  exported_files: { source_path: string; destination_path: string }[];
  skipped_files: { source_path: string; reason: string }[];
  total_exported: number;
  total_skipped: number;
}

/**
 * Export every photo containing the given people into a person-named
 * subfolder under `destinationRoot`.
 *
 * Same AND semantics as search — see searchPhotosByPersons. The
 * backend creates the person-named folder itself (e.g. "Alice" or
 * "Alice_Bob"); this function just reports back where it went and
 * what happened, per-file, so the UI can show a real summary rather
 * than a generic "Done."
 *
 * @param personIds One or more Person ids to export photos for.
 * @param destinationRoot An absolute path to an existing, writable
 *   folder on the user's machine. The backend validates this and
 *   returns a 422 (surfaced as ApiError) if it doesn't exist or can't
 *   be written to.
 */
export async function exportPhotosByPersons(
  personIds: number[],
  destinationRoot: string
): Promise<ExportResult> {
  if (personIds.length === 0) {
    throw new Error("exportPhotosByPersons requires at least one person id.");
  }

  try {
    const response = await apiClient.post<RawExportResponse>("/export/photos", {
      person_ids: personIds,
      destination_root: destinationRoot,
    });

    return {
      outputFolder: response.data.output_folder,
      exportedFiles: response.data.exported_files.map((file) => ({
        sourcePath: file.source_path,
        destinationPath: file.destination_path,
      })),
      skippedFiles: response.data.skipped_files.map((file) => ({
        sourcePath: file.source_path,
        reason: file.reason,
      })),
      totalExported: response.data.total_exported,
      totalSkipped: response.data.total_skipped,
    };
  } catch (error) {
    throw toApiError(error);
  }
}
