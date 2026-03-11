import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import SubscriptionOption from "./SubscriptionOption";

describe("SubscriptionOption", () => {
  it("renders correctly with fire zone unit name", () => {
    const fireZoneUnit = "Kamloops Fire Zone";
    render(<SubscriptionOption fireZoneUnit={fireZoneUnit} />);
    expect(screen.getByText("Kamloops")).toBeInTheDocument();
  });

  it("renders switch component", () => {
    render(<SubscriptionOption fireZoneUnit="Test Zone" />);
    expect(screen.getByRole("checkbox")).toBeInTheDocument();
  });

  it("toggles switch when row is clicked", () => {
    render(<SubscriptionOption fireZoneUnit="Test Zone" />);
    const switchComponent = screen.getByRole("checkbox");

    // Initially unchecked
    expect(switchComponent).not.toBeChecked();

    // Click the row
    fireEvent.click(screen.getByText(/test zone/i));

    // Now should be checked
    expect(switchComponent).toBeChecked();

    // Click again to toggle back
    fireEvent.click(screen.getByText(/test zone/i));
    expect(switchComponent).not.toBeChecked();
  });

  it("toggles switch when switch is clicked directly", () => {
    render(<SubscriptionOption fireZoneUnit="Test Zone" />);
    const switchComponent = screen.getByRole("checkbox");

    // Initially unchecked
    expect(switchComponent).not.toBeChecked();

    // Click the switch
    fireEvent.click(switchComponent);

    // Now should be checked
    expect(switchComponent).toBeChecked();

    // Click again to toggle back
    fireEvent.click(switchComponent);
    expect(switchComponent).not.toBeChecked();
  });
});
