import { beforeEach, describe, expect, it, vi } from "vitest";

import { exportPhotosByPersons } from "@/lib/api/export";

const postMock = vi.fn();

vi.mock("@/lib/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/client")>("@/lib/api/client");
  return {
    ...actual,
    apiClient: { post: (...args: unknown[]) => postMock(...args) },
  };
});

describe("exportPhotosByPersons", () => {
  beforeEach(() => {
    postMock.mockReset();
  });

  it("rejects an empty person id list without making a network call", async () => {
    await expect(exportPhotosByPersons([], "/tmp/out")).rejects.toThrow(/at least one/i);
    expect(postMock).not.toHaveBeenCalled();
  });

  it("sends snake_case body and maps the response back to camelCase", async () => {
    postMock.mockResolvedValueOnce({
      data: {
        output_folder: "/tmp/out/Alice",
        exported_files: [{ source_path: "/src/a.jpg", destination_path: "/tmp/out/Alice/a.jpg" }],
        skipped_files: [{ source_path: "/src/b.jpg", reason: "Source file no longer exists on disk" }],
        total_exported: 1,
        total_skipped: 1,
      },
    });

    const result = await exportPhotosByPersons([1], "/tmp/out");

    expect(postMock).toHaveBeenCalledWith("/export/photos", {
      person_ids: [1],
      destination_root: "/tmp/out",
    });
    expect(result.outputFolder).toBe("/tmp/out/Alice");
    expect(result.totalExported).toBe(1);
    expect(result.totalSkipped).toBe(1);
    expect(result.skippedFiles[0].reason).toBe("Source file no longer exists on disk");
  });

  it("propagates a normalized ApiError for a bad destination", async () => {
    postMock.mockRejectedValueOnce({
      isAxiosError: true,
      response: {
        status: 422,
        data: { error: { code: "VALIDATION_FAILED", message: "Destination folder does not exist" } },
      },
    });

    await expect(exportPhotosByPersons([1], "/nope")).rejects.toMatchObject({
      code: "VALIDATION_FAILED",
    });
  });
});
