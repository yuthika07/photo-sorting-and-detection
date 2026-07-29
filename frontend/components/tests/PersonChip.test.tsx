import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PersonChip } from "@/components/search/PersonChip";

describe("PersonChip", () => {
  it("renders the label", () => {
    render(<PersonChip label="Bride" onRemove={vi.fn()} />);
    expect(screen.getByText("Bride")).toBeInTheDocument();
  });

  it("calls onRemove when the remove button is clicked", async () => {
    const onRemove = vi.fn();
    render(<PersonChip label="Bride" onRemove={onRemove} />);

    await userEvent.click(screen.getByRole("button", { name: /remove bride/i }));

    expect(onRemove).toHaveBeenCalledTimes(1);
  });
});
