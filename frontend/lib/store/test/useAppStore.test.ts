import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/client";

const searchMock = vi.fn();
const listPersonsMock = vi.fn();
const renamePersonApiMock = vi.fn();
const exportMock = vi.fn();

vi.mock("@/lib/api/search", () => ({ searchPhotosByPersons: (...args: unknown[]) => searchMock(...args) }));
vi.mock("@/lib/api/persons", () => ({
  listPersons: (...args: unknown[]) => listPersonsMock(...args),
  renamePerson: (...args: unknown[]) => renamePersonApiMock(...args),
}));
vi.mock("@/lib/api/export", () => ({ exportPhotosByPersons: (...args: unknown[]) => exportMock(...args) }));

// Imported AFTER the mocks above so the store picks up the mocked modules
const { useAppStore } = await import("@/lib/store/useAppStore");

function resetStore() {
  useAppStore.setState({
    people: [],
    peopleStatus: "idle",
    peopleError: null,
    selectedPersonIds: [],
    photos: [],
    searchStatus: "idle",
    searchError: null,
    exportStatus: "idle",
    exportError: null,
    lastExportResult: null,
  });
}

describe("useAppStore", () => {
  beforeEach(() => {
    searchMock.mockReset();
    listPersonsMock.mockReset();
    renamePersonApiMock.mockReset();
    exportMock.mockReset();
    resetStore();
  });

  describe("loadPeople", () => {
    it("populates people on success", async () => {
      listPersonsMock.mockResolvedValueOnce([
        { id: 1, displayName: "Alice", photoCount: 3, thumbnailUrl: null, isConfirmed: true },
      ]);

      await useAppStore.getState().loadPeople();

      expect(useAppStore.getState().peopleStatus).toBe("ready");
      expect(useAppStore.getState().people).toHaveLength(1);
    });

    it("sets an error status on failure instead of throwing", async () => {
      listPersonsMock.mockRejectedValueOnce(new ApiError("boom", "NETWORK_ERROR", null));

      await useAppStore.getState().loadPeople();

      expect(useAppStore.getState().peopleStatus).toBe("error");
      expect(useAppStore.getState().peopleError).toBe("boom");
    });
  });

  describe("selection + instant filtering", () => {
    it("selecting a person immediately triggers a search", async () => {
      searchMock.mockResolvedValueOnce({
        persons: [{ id: 1, displayName: "Alice" }],
        photos: [{ id: 10, filePath: "/a.jpg", takenAt: null, width: null, height: null }],
        totalPhotos: 1,
      });

      useAppStore.getState().togglePersonSelected(1);
      // togglePersonSelected fires the search asynchronously; flush microtasks
      await vi.waitFor(() => expect(useAppStore.getState().searchStatus).toBe("ready"));

      expect(searchMock).toHaveBeenCalledWith([1]);
      expect(useAppStore.getState().selectedPersonIds).toEqual([1]);
      expect(useAppStore.getState().photos).toHaveLength(1);
    });

    it("selecting a second person re-runs search with BOTH ids (AND semantics)", async () => {
      searchMock.mockResolvedValue({ persons: [], photos: [], totalPhotos: 0 });

      useAppStore.getState().togglePersonSelected(1);
      await vi.waitFor(() => expect(searchMock).toHaveBeenCalledTimes(1));

      useAppStore.getState().togglePersonSelected(2);
      await vi.waitFor(() => expect(searchMock).toHaveBeenCalledTimes(2));

      expect(searchMock).toHaveBeenLastCalledWith([1, 2]);
    });

    it("toggling an already-selected person removes it and re-searches", async () => {
      searchMock.mockResolvedValue({ persons: [], photos: [], totalPhotos: 0 });
      useAppStore.setState({ selectedPersonIds: [1, 2] });

      useAppStore.getState().togglePersonSelected(1);
      await vi.waitFor(() => expect(searchMock).toHaveBeenCalledWith([2]));

      expect(useAppStore.getState().selectedPersonIds).toEqual([2]);
    });

    it("removing the last selected person clears results without calling search", async () => {
      useAppStore.setState({ selectedPersonIds: [1], photos: [{ id: 1 } as never], searchStatus: "ready" });

      useAppStore.getState().removePersonSelected(1);
      await vi.waitFor(() => expect(useAppStore.getState().searchStatus).toBe("idle"));

      expect(searchMock).not.toHaveBeenCalled();
      expect(useAppStore.getState().photos).toEqual([]);
    });

    it("clearSelection resets selection and results synchronously", () => {
      useAppStore.setState({ selectedPersonIds: [1, 2], photos: [{ id: 1 } as never] });

      useAppStore.getState().clearSelection();

      expect(useAppStore.getState().selectedPersonIds).toEqual([]);
      expect(useAppStore.getState().photos).toEqual([]);
    });

    it("a failed search sets an error state rather than throwing", async () => {
      searchMock.mockRejectedValueOnce(new ApiError("search broke", "UNKNOWN_ERROR", 500));

      useAppStore.getState().togglePersonSelected(1);
      await vi.waitFor(() => expect(useAppStore.getState().searchStatus).toBe("error"));

      expect(useAppStore.getState().searchError).toBe("search broke");
    });
  });

  describe("renamePerson", () => {
    it("patches only the renamed person in the people list", async () => {
      useAppStore.setState({
        people: [
          { id: 1, displayName: "Old Name", photoCount: 2, thumbnailUrl: null, isConfirmed: true },
          { id: 2, displayName: "Bob", photoCount: 1, thumbnailUrl: null, isConfirmed: true },
        ],
      });
      renamePersonApiMock.mockResolvedValueOnce({
        id: 1,
        displayName: "New Name",
        photoCount: 2,
        thumbnailUrl: null,
        isConfirmed: true,
      });

      await useAppStore.getState().renamePerson(1, "New Name");

      const people = useAppStore.getState().people;
      expect(people.find((p) => p.id === 1)?.displayName).toBe("New Name");
      expect(people.find((p) => p.id === 2)?.displayName).toBe("Bob"); // untouched
    });

    it("rethrows on failure so the UI can keep the dialog open", async () => {
      renamePersonApiMock.mockRejectedValueOnce(new ApiError("rename failed", "UNKNOWN_ERROR", 500));

      await expect(useAppStore.getState().renamePerson(1, "X")).rejects.toThrow("rename failed");
    });
  });

  describe("exportSelected", () => {
    it("does nothing when nothing is selected", async () => {
      await useAppStore.getState().exportSelected("/tmp/out");
      expect(exportMock).not.toHaveBeenCalled();
    });

    it("sets success state with the result on success", async () => {
      useAppStore.setState({ selectedPersonIds: [1] });
      exportMock.mockResolvedValueOnce({
        outputFolder: "/tmp/out/Alice",
        exportedFiles: [],
        skippedFiles: [],
        totalExported: 3,
        totalSkipped: 0,
      });

      await useAppStore.getState().exportSelected("/tmp/out");

      expect(useAppStore.getState().exportStatus).toBe("success");
      expect(useAppStore.getState().lastExportResult?.totalExported).toBe(3);
    });

    it("sets error state on failure", async () => {
      useAppStore.setState({ selectedPersonIds: [1] });
      exportMock.mockRejectedValueOnce(new ApiError("Destination not writable", "VALIDATION_FAILED", 422));

      await useAppStore.getState().exportSelected("/tmp/out");

      expect(useAppStore.getState().exportStatus).toBe("error");
      expect(useAppStore.getState().exportError).toBe("Destination not writable");
    });

    it("dismissExportResult clears export state", () => {
      useAppStore.setState({ exportStatus: "success", lastExportResult: { totalExported: 1 } as never });

      useAppStore.getState().dismissExportResult();

      expect(useAppStore.getState().exportStatus).toBe("idle");
      expect(useAppStore.getState().lastExportResult).toBeNull();
    });
  });
});
