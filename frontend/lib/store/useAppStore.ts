import { create } from "zustand";

import { exportPhotosByPersons } from "@/lib/api/export";
import { listPersons, renamePerson as renamePersonApi } from "@/lib/api/persons";
import { searchPhotosByPersons } from "@/lib/api/search";
import { ApiError } from "@/lib/api/client";
import type { ExportResult, Person, Photo } from "@/lib/types";

/**
 * Why Zustand (and not just React Context) — per this project's brief
 * ("use Context if sufficient; Zustand if state becomes complex"):
 * this store has several pieces of state that all change independently
 * AND several async actions that need to read/update more than one of
 * them at once (selecting a person re-triggers a search; renaming a
 * person needs to patch both the `people` list AND any occurrence of
 * that person already sitting inside `searchResult`). Modeling that
 * with plain Context would mean either one giant reducer or several
 * nested providers coordinating with each other — Zustand gives one
 * flat store with real actions, which is a much better fit here.
 */

interface AppState {
  // --- People shelf -------------------------------------------------
  people: Person[];
  peopleStatus: "idle" | "loading" | "error" | "ready";
  peopleError: string | null;

  // --- Selection (drives the search chips) ---------------------------
  selectedPersonIds: number[];

  // --- Search results --------------------------------------------------
  photos: Photo[];
  searchStatus: "idle" | "loading" | "error" | "ready";
  searchError: string | null;

  // --- Export ------------------------------------------------------------
  exportStatus: "idle" | "loading" | "error" | "success";
  exportError: string | null;
  lastExportResult: ExportResult | null;

  // --- Actions -------------------------------------------------------------
  loadPeople: () => Promise<void>;
  togglePersonSelected: (personId: number) => void;
  removePersonSelected: (personId: number) => void;
  clearSelection: () => void;
  renamePerson: (personId: number, displayName: string) => Promise<void>;
  exportSelected: (destinationRoot: string) => Promise<void>;
  dismissExportResult: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
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

  loadPeople: async () => {
    set({ peopleStatus: "loading", peopleError: null });
    try {
      const people = await listPersons();
      set({ people, peopleStatus: "ready" });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Couldn't load people.";
      set({ peopleStatus: "error", peopleError: message });
    }
  },

  togglePersonSelected: (personId: number) => {
    const current = get().selectedPersonIds;
    const next = current.includes(personId)
      ? current.filter((id) => id !== personId)
      : [...current, personId];
    set({ selectedPersonIds: next });
    void runSearch(next, set);
  },

  removePersonSelected: (personId: number) => {
    const next = get().selectedPersonIds.filter((id) => id !== personId);
    set({ selectedPersonIds: next });
    void runSearch(next, set);
  },

  clearSelection: () => {
    set({ selectedPersonIds: [], photos: [], searchStatus: "idle", searchError: null });
  },

  renamePerson: async (personId: number, displayName: string) => {
    try {
      const updated = await renamePersonApi(personId, displayName);
      set((state) => ({
        people: state.people.map((person) => (person.id === personId ? updated : person)),
      }));
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Couldn't rename this person.";
      set({ peopleError: message });
      throw error;
    }
  },

  exportSelected: async (destinationRoot: string) => {
    const { selectedPersonIds } = get();
    if (selectedPersonIds.length === 0) return;

    set({ exportStatus: "loading", exportError: null });
    try {
      const result = await exportPhotosByPersons(selectedPersonIds, destinationRoot);
      set({ exportStatus: "success", lastExportResult: result });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Export failed.";
      set({ exportStatus: "error", exportError: message });
    }
  },

  dismissExportResult: () => {
    set({ exportStatus: "idle", exportError: null, lastExportResult: null });
  },
}));

/**
 * Shared by togglePersonSelected/removePersonSelected — "instant
 * filtering" means every selection change re-runs the search
 * immediately, with an empty selection clearing results rather than
 * calling an API that requires at least one id.
 */
async function runSearch(personIds: number[], set: (partial: Partial<AppState>) => void): Promise<void> {
  if (personIds.length === 0) {
    set({ photos: [], searchStatus: "idle", searchError: null });
    return;
  }

  set({ searchStatus: "loading", searchError: null });
  try {
    const result = await searchPhotosByPersons(personIds);
    set({ photos: result.photos, searchStatus: "ready" });
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "Search failed.";
    set({ searchStatus: "error", searchError: message });
  }
}
