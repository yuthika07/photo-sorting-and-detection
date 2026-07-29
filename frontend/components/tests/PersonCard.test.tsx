import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PersonCard } from "@/components/people/PersonCard";
import type { Person } from "@/lib/types";

const person: Person = {
  id: 1,
  displayName: "Bride",
  photoCount: 12,
  thumbnailUrl: null,
  isConfirmed: true,
};

describe("PersonCard", () => {
  it("renders the name and photo count", () => {
    render(
      <PersonCard person={person} selected={false} onToggleSelect={vi.fn()} onRename={vi.fn()} onExport={vi.fn()} />
    );

    expect(screen.getByText("Bride")).toBeInTheDocument();
    expect(screen.getByText("12 photos")).toBeInTheDocument();
  });

  it("uses singular '1 photo' for a count of exactly one", () => {
    render(
      <PersonCard
        person={{ ...person, photoCount: 1 }}
        selected={false}
        onToggleSelect={vi.fn()}
        onRename={vi.fn()}
        onExport={vi.fn()}
      />
    );

    expect(screen.getByText("1 photo")).toBeInTheDocument();
  });

  it("calls onToggleSelect with the person id when the card is clicked", async () => {
    const onToggleSelect = vi.fn();
    render(
      <PersonCard
        person={person}
        selected={false}
        onToggleSelect={onToggleSelect}
        onRename={vi.fn()}
        onExport={vi.fn()}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: /bride/i, pressed: false }));

    expect(onToggleSelect).toHaveBeenCalledWith(1);
  });

  it("reflects selected state via aria-pressed", () => {
    render(
      <PersonCard person={person} selected={true} onToggleSelect={vi.fn()} onRename={vi.fn()} onExport={vi.fn()} />
    );

    expect(screen.getByRole("button", { name: /bride/i })).toHaveAttribute("aria-pressed", "true");
  });

  it("Rename and Export buttons do NOT toggle selection (event isolation)", async () => {
    const onToggleSelect = vi.fn();
    const onRename = vi.fn();
    const onExport = vi.fn();
    render(
      <PersonCard
        person={person}
        selected={false}
        onToggleSelect={onToggleSelect}
        onRename={onRename}
        onExport={onExport}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: "Rename" }));
    await userEvent.click(screen.getByRole("button", { name: "Export" }));

    expect(onRename).toHaveBeenCalledWith(person);
    expect(onExport).toHaveBeenCalledWith(person);
    expect(onToggleSelect).not.toHaveBeenCalled();
  });

  it("falls back to 'Unnamed' when displayName is null", () => {
    render(
      <PersonCard
        person={{ ...person, displayName: null }}
        selected={false}
        onToggleSelect={vi.fn()}
        onRename={vi.fn()}
        onExport={vi.fn()}
      />
    );

    expect(screen.getByText("Unnamed")).toBeInTheDocument();
  });
});
