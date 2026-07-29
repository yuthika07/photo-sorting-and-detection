import { beforeEach, describe, expect, it, vi } from "vitest";

import { searchPhotosByPersons } from "@/lib/api/search";

const getMock = vi.fn();

vi.mock("@/lib/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/client")>("@/lib/api/client");
  return {
    ...actual,
    apiClient: { get: (...args: unknown[]) => getMock(...args) },
  };
});

describe("searchPhotosByPersons", () => {
  beforeEach(() => {
    getMock.mockReset();
  });

  it("rejects an empty person id list without making a network call", async () => {
    await expect(searchPhotosByPersons([])).rejects.toThrow(/at least one/i);
    expect(getMock).not.toHaveBeenCalled();
  });

  it("sends person_ids as the query param and maps snake_case to camelCase", async () => {
    getMock.mockResolvedValueOnce({
      data: {
        persons: [{ id: 1, display_name: "Alice" }],
        photos: [
          { id: 10, file_path: "/a.jpg", taken_at: "2026-06-01T10:00:00", width: 800, height: 600 },
        ],
        total_photos: 1,
      },
    });

    const result = await searchPhotosByPersons([1, 2]);

    expect(getMock).toHaveBeenCalledWith("/search/photos", { params: { person_ids: [1, 2] } });
    expect(result.persons).toEqual([{ id: 1, displayName: "Alice" }]);
    expect(result.photos[0]).toMatchObject({ id: 10, filePath: "/a.jpg", width: 800, height: 600 });
    expect(result.totalPhotos).toBe(1);
  });

  it("propagates a normalized ApiError on failure", async () => {
    getMock.mockRejectedValueOnce({
      isAxiosError: true,
      response: { status: 404, data: { error: { code: "NOT_FOUND", message: "No person found" } } },
    });

    await expect(searchPhotosByPersons([999])).rejects.toMatchObject({
      code: "NOT_FOUND",
      message: "No person found",
    });
  });
});
