import { apiClient, toApiError } from "@/lib/api/client";
import type { Person } from "@/lib/types";

/**
 * IMPORTANT — assumed backend contract.
 *
 * The backend built so far (see backend/README.md) only exposes
 * `GET /search/photos` and `POST /export/photos`. There is no
 * "list all people" or "rename a person" endpoint yet — this phase is
 * frontend-only, per the request that started it.
 *
 * The two functions below are written against the endpoints this UI
 * needs to exist:
 *   GET   /persons              -> Person[]
 *   PATCH /persons/{id}         -> { display_name: string } -> Person
 *
 * shaped consistently with the rest of the backend (same snake_case
 * JSON convention, same AppException error envelope), so wiring them
 * up later is a small backend addition, not a frontend rewrite. Until
 * that endpoint exists, calls through this module will fail with a
 * network/404 ApiError — components using it (PersonShelf) already
 * render that as a normal empty/error state rather than crashing.
 */

interface RawPerson {
  id: number;
  display_name: string | null;
  photo_count: number;
  thumbnail_url: string | null;
  is_confirmed: boolean;
}

function mapPerson(raw: RawPerson): Person {
  return {
    id: raw.id,
    displayName: raw.display_name,
    photoCount: raw.photo_count,
    thumbnailUrl: raw.thumbnail_url,
    isConfirmed: raw.is_confirmed,
  };
}

/** Fetch every known person, for the People shelf. */
export async function listPersons(): Promise<Person[]> {
  try {
    const response = await apiClient.get<RawPerson[]>("/persons");
    return response.data.map(mapPerson);
  } catch (error) {
    throw toApiError(error);
  }
}

/** Rename a person (the PersonCard's rename action). */
export async function renamePerson(personId: number, displayName: string): Promise<Person> {
  try {
    const response = await apiClient.patch<RawPerson>(`/persons/${personId}`, {
      display_name: displayName,
    });
    return mapPerson(response.data);
  } catch (error) {
    throw toApiError(error);
  }
}
