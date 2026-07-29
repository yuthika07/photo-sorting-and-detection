"use client";

import { AnimatePresence } from "framer-motion";
import { Plus, Search } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { PersonChip } from "@/components/search/PersonChip";
import { useAppStore } from "@/lib/store/useAppStore";

/**
 * The search row: selected people appear as removable gold chips
 * (e.g. "Bride", "Bride" + "Groom", "Bride" + "Mother" — the exact
 * examples from the brief), sitting inside a recessed "well" the same
 * way the People shelf's rail is recessed, so the whole toolbar reads
 * as one consistent physical surface. Every chip add/remove instantly
 * re-runs the search — see useAppStore's togglePersonSelected /
 * removePersonSelected, there's no separate "Search" button to press.
 */
export function SearchBar() {
  const people = useAppStore((state) => state.people);
  const selectedPersonIds = useAppStore((state) => state.selectedPersonIds);
  const togglePersonSelected = useAppStore((state) => state.togglePersonSelected);
  const removePersonSelected = useAppStore((state) => state.removePersonSelected);
  const clearSelection = useAppStore((state) => state.clearSelection);

  const [addMenuOpen, setAddMenuOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedPeople = selectedPersonIds
    .map((id) => people.find((person) => person.id === id))
    .filter((person): person is NonNullable<typeof person> => Boolean(person));

  const availablePeople = people.filter((person) => !selectedPersonIds.includes(person.id));

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setAddMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="flex items-center gap-3 px-5 py-3">
      <Search size={15} className="shrink-0 text-steel-400" />

      <div className="well-surface flex min-h-9 flex-1 flex-wrap items-center gap-1.5 rounded-lg px-2.5 py-1.5">
        <AnimatePresence initial={false}>
          {selectedPeople.map((person) => (
            <PersonChip
              key={person.id}
              label={person.displayName ?? "Unnamed"}
              onRemove={() => removePersonSelected(person.id)}
            />
          ))}
        </AnimatePresence>

        {selectedPeople.length === 0 && (
          <span className="px-1 text-[13px] text-steel-500">Select people to filter photos…</span>
        )}

        <div className="relative ml-auto" ref={containerRef}>
          <button
            type="button"
            onClick={() => setAddMenuOpen((open) => !open)}
            disabled={availablePeople.length === 0}
            className="flex items-center gap-1 rounded-full border border-graphite-600 bg-graphite-800 px-2.5 py-1 text-[12px] text-steel-300 transition-colors hover:bg-graphite-700 disabled:opacity-30"
          >
            <Plus size={12} />
            Add
          </button>

          {addMenuOpen && availablePeople.length > 0 && (
            <div className="absolute right-0 top-full z-20 mt-1.5 max-h-56 w-44 overflow-y-auto rounded-lg border border-graphite-600 bg-graphite-800 p-1 shadow-panel">
              {availablePeople.map((person) => (
                <button
                  key={person.id}
                  type="button"
                  onClick={() => {
                    togglePersonSelected(person.id);
                    setAddMenuOpen(false);
                  }}
                  className="w-full rounded-md px-2.5 py-1.5 text-left text-[13px] text-steel-300 transition-colors hover:bg-graphite-700 hover:text-white"
                >
                  {person.displayName ?? "Unnamed"}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {selectedPeople.length > 0 && (
        <button
          type="button"
          onClick={clearSelection}
          className="shrink-0 text-[12.5px] font-medium text-steel-400 transition-colors hover:text-steel-200"
        >
          Clear
        </button>
      )}
    </div>
  );
}
