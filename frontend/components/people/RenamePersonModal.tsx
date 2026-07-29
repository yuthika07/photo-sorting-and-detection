"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import type { Person } from "@/lib/types";

interface RenamePersonModalProps {
  person: Person | null;
  onClose: () => void;
  onSubmit: (name: string) => Promise<void>;
}

export function RenamePersonModal({ person, onClose, onSubmit }: RenamePersonModalProps) {
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setName(person?.displayName ?? "");
  }, [person]);

  async function handleSubmit() {
    const trimmed = name.trim();
    if (!trimmed) return;
    setSubmitting(true);
    try {
      await onSubmit(trimmed);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal open={person !== null} onClose={onClose} title="Rename person">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void handleSubmit();
        }}
      >
        <label htmlFor="person-name" className="mb-1.5 block text-[12px] font-medium text-ink-700">
          Name
        </label>
        <input
          id="person-name"
          autoFocus
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="e.g. Bride, Groom, Mother of the Bride"
          className="w-full rounded-md border border-paper-300 bg-white px-3 py-2 text-sm text-ink-900 shadow-[inset_0_1px_2px_rgba(38,36,32,0.08)] outline-none focus:border-gold-500 focus:ring-2 focus:ring-gold-500/25"
        />
        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="subtle" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="brass" disabled={!name.trim() || submitting}>
            {submitting ? "Saving…" : "Save"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
