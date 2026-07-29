"use client";

import { AlertCircle, Loader2, Users } from "lucide-react";
import { useEffect, useState } from "react";

import { PersonCard } from "@/components/people/PersonCard";
import { RenamePersonModal } from "@/components/people/RenamePersonModal";
import { useAppStore } from "@/lib/store/useAppStore";
import type { Person } from "@/lib/types";

/**
 * The horizontal "catalog rail" of people, styled as a recessed well
 * (see .well-surface in globals.css) that the paper PersonCards sit
 * inside of — like prints propped in a physical sorting tray.
 */
export function PersonShelf() {
  const people = useAppStore((state) => state.people);
  const peopleStatus = useAppStore((state) => state.peopleStatus);
  const peopleError = useAppStore((state) => state.peopleError);
  const selectedPersonIds = useAppStore((state) => state.selectedPersonIds);
  const loadPeople = useAppStore((state) => state.loadPeople);
  const togglePersonSelected = useAppStore((state) => state.togglePersonSelected);
  const renamePerson = useAppStore((state) => state.renamePerson);
  const exportSelected = useAppStore((state) => state.exportSelected);

  const [personBeingRenamed, setPersonBeingRenamed] = useState<Person | null>(null);

  useEffect(() => {
    void loadPeople();
  }, [loadPeople]);

  async function handleQuickExport(person: Person) {
    // A native folder-picker isn't available from a plain browser
    // context — in the packaged desktop shell this would open a real
    // OS folder dialog instead. window.prompt is a deliberate, clearly
    // temporary stand-in so the export flow is still fully exercised
    // end to end from the UI.
    const destination = window.prompt(
      `Export "${person.displayName ?? "this person"}"'s photos to which folder?`,
      "/Users/me/Desktop/wedding_export"
    );
    if (!destination) return;

    togglePersonSelected(person.id);
    await exportSelected(destination);
  }

  return (
    <section aria-label="People">
      <div className="flex items-center gap-2 px-5 pt-1 pb-2">
        <Users size={14} className="text-steel-400" />
        <h2 className="text-[11px] font-semibold uppercase tracking-[0.12em] text-steel-400">People</h2>
      </div>

      <div className="well-surface mx-4 mb-4 rounded-lg px-3 py-3">
        {peopleStatus === "loading" && (
          <div className="flex items-center gap-2 px-2 py-6 text-steel-400 text-sm">
            <Loader2 size={15} className="animate-spin" />
            Loading people…
          </div>
        )}

        {peopleStatus === "error" && (
          <div className="flex items-center gap-2 px-2 py-6 text-gold-400 text-sm">
            <AlertCircle size={15} />
            {peopleError ?? "Couldn't load people."}
          </div>
        )}

        {peopleStatus === "ready" && people.length === 0 && (
          <div className="px-2 py-6 text-steel-400 text-sm">
            No people found yet. Import and process some photos first.
          </div>
        )}

        {peopleStatus === "ready" && people.length > 0 && (
          <div className="flex gap-3 overflow-x-auto pb-1">
            {people.map((person) => (
              <PersonCard
                key={person.id}
                person={person}
                selected={selectedPersonIds.includes(person.id)}
                onToggleSelect={togglePersonSelected}
                onRename={setPersonBeingRenamed}
                onExport={handleQuickExport}
              />
            ))}
          </div>
        )}
      </div>

      <RenamePersonModal
        person={personBeingRenamed}
        onClose={() => setPersonBeingRenamed(null)}
        onSubmit={async (name) => {
          if (!personBeingRenamed) return;
          await renamePerson(personBeingRenamed.id, name);
          setPersonBeingRenamed(null);
        }}
      />
    </section>
  );
}
