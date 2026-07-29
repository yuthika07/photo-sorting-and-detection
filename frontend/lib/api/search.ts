import { apiClient, toApiError } from "@/lib/api/client";
import type { Photo, PersonSummary, SearchPhotosResult } from "@/lib/types";

/** Raw shape actually returned by GET /search/photos (app/schemas/search.py). */
interface RawSearchResponse {
  persons: { id: number; display_name: string | null }[];
  photos: {
    id: number;
    file_path: string;
    taken_at: string | null;
    width: number | null;
    height: number | null;
  }[];
  total_photos: number;
}

/**
 * Search for photos containing every one of the given people.
 *
 * Mirrors the backend's AND semantics exactly (see
 * backend/app/db/repositories/photo_repository.py's
 * search_by_person_ids): passing a single id searches by one person;
 * passing several requires ALL of them to appear together.
 *
 * @param personIds One or more Person ids. Must be non-empty — the
 *   backend rejects an empty list with a 422, so this function does
 *   too, before ever making a network call.
 */
export async function searchPhotosByPersons(personIds: number[]): Promise<SearchPhotosResult> {
  if (personIds.length === 0) {
    throw new Error("searchPhotosByPersons requires at least one person id.");
  }

  try {
    const response = await apiClient.get<RawSearchResponse>("/search/photos", {
      // Axios serializes a repeated array param as person_ids=1&person_ids=2,
      // matching exactly what the FastAPI Query(...) parameter expects.
      params: { person_ids: personIds },
    });

    const persons: PersonSummary[] = response.data.persons.map((person) => ({
      id: person.id,
      displayName: person.display_name,
    }));

    const photos: Photo[] = response.data.photos.map((photo) => ({
      id: photo.id,
      filePath: photo.file_path,
      takenAt: photo.taken_at,
      width: photo.width,
      height: photo.height,
    }));

    return { persons, photos, totalPhotos: response.data.total_photos };
  } catch (error) {
    throw toApiError(error);
  }
}
