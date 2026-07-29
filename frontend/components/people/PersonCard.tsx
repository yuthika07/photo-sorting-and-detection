"use client";

import { motion } from "framer-motion";
import { Download, Pencil, User } from "lucide-react";

import { Button } from "@/components/ui/Button";
import type { Person } from "@/lib/types";

interface PersonCardProps {
  person: Person;
  selected: boolean;
  onToggleSelect: (personId: number) => void;
  onRename: (person: Person) => void;
  onExport: (person: Person) => void;
}

/**
 * One person, styled as a physical photo print propped in the
 * catalog shelf: a thumbnail "photograph" with a paper mount below it
 * carrying the name, count, and two tactile action buttons.
 *
 * Selection is the one place this app spends its single gold accent —
 * per the brief, a gold border + soft shadow + slight lift, and
 * nowhere else, so selection stays unmistakable.
 */
export function PersonCard({ person, selected, onToggleSelect, onRename, onExport }: PersonCardProps) {
  const photoCountLabel = person.photoCount === 1 ? "1 photo" : `${person.photoCount} photos`;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: selected ? -3 : 0 }}
      whileHover={{ y: -3 }}
      transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
      className="w-40 shrink-0 select-none"
    >
      <button
        type="button"
        onClick={() => onToggleSelect(person.id)}
        aria-pressed={selected}
        className={[
          "group w-full rounded-xl paper-surface border p-2 pb-3 text-left transition-shadow duration-200",
          selected
            ? "border-gold-500 shadow-[0_0_0_3px_rgba(201,162,39,0.22),0_10px_22px_-8px_rgba(38,36,32,0.35)]"
            : "border-paper-300 shadow-card hover:shadow-card-elevated",
        ].join(" ")}
      >
        <div className="aspect-square w-full overflow-hidden rounded-lg border border-black/5 bg-graphite-900 shadow-inner">
          {person.thumbnailUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={person.thumbnailUrl}
              alt={person.displayName ?? "Unnamed person"}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-steel-500">
              <User size={36} strokeWidth={1.5} />
            </div>
          )}
        </div>

        <div className="mt-2.5 px-0.5">
          <p className="truncate text-[13.5px] font-semibold text-ink-900">
            {person.displayName ?? "Unnamed"}
          </p>
          <p className="text-[11.5px] text-ink-500">{photoCountLabel}</p>
        </div>
      </button>

      <div className="mt-2 flex gap-1.5 px-0.5">
        <Button
          variant="subtle"
          size="sm"
          className="flex-1"
          icon={<Pencil size={13} />}
          onClick={(event) => {
            event.stopPropagation();
            onRename(person);
          }}
        >
          Rename
        </Button>
        <Button
          variant="subtle"
          size="sm"
          className="flex-1"
          icon={<Download size={13} />}
          onClick={(event) => {
            event.stopPropagation();
            onExport(person);
          }}
        >
          Export
        </Button>
      </div>
    </motion.div>
  );
}
