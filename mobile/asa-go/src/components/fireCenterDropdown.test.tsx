import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import FireCenterDropdown from "@/components/FireCenterDropdown";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { FireCenter, FireShape } from "@/api/fbaAPI";
import React from "react";

// Sample fire centers
const fireCenters: FireCenter[] = [
  { id: 1, name: "Fire Center 1", stations: [] },
  { id: 2, name: "Fire Center 2", stations: [] },
];

describe("FireCenterDropdown", () => {
  let setSelectedFireCenter: React.Dispatch<React.SetStateAction<FireCenter | undefined>>;
  let setSelectedFireShape: React.Dispatch<React.SetStateAction<FireShape | undefined>>;

  beforeEach(() => {
    setSelectedFireCenter = vi.fn();
    setSelectedFireShape = vi.fn();
  });

  it("renders with provided options", () => {
    render(
      <FireCenterDropdown
        fireCenterOptions={fireCenters}
        selectedFireCenter={undefined}
        setSelectedFireCenter={setSelectedFireCenter}
        setSelectedFireShape={setSelectedFireShape}
      />
    );

    expect(screen.getByLabelText("Select Fire Centre")).toBeInTheDocument();
  });

  it("calls setSelectedFireCenter and setSelectedFireShape on selection", () => {
    render(
      <FireCenterDropdown
        fireCenterOptions={fireCenters}
        selectedFireCenter={undefined}
        setSelectedFireCenter={setSelectedFireCenter}
        setSelectedFireShape={setSelectedFireShape}
      />
    );

    screen.debug()

    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "Fire Center 1" } });
    fireEvent.keyDown(input, { key: "ArrowDown" });
    fireEvent.keyDown(input, { key: "Enter" });
    screen.debug()

    expect(setSelectedFireShape).toHaveBeenCalledWith(undefined);
    expect(setSelectedFireCenter).toHaveBeenCalledWith(
      expect.objectContaining({ name: "Fire Center 1" })
    );
  });

  it("clears selection", () => {
    render(
      <FireCenterDropdown
        fireCenterOptions={fireCenters}
        selectedFireCenter={fireCenters[0]}
        setSelectedFireCenter={setSelectedFireCenter}
        setSelectedFireShape={setSelectedFireShape}
      />
    );

    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "" } });
    fireEvent.keyDown(input, { key: "Backspace" });

    waitFor(() => expect(input).toHaveValue(""))
  });
});
