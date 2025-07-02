import { fireEvent, render, screen } from "@testing-library/react";
import { DateTime } from "luxon";
import { describe, expect, it, vi } from "vitest";
import TodayTomorrowSwitch from "./TodayTomorrowSwitch";

describe("TodayTomorrowSwitch", () => {
  it("renders both buttons", () => {
    const mockSetDate = vi.fn();
    const today = DateTime.now();

    render(<TodayTomorrowSwitch date={today} setDate={mockSetDate} />);

    expect(screen.getByText("NOW")).toBeInTheDocument();
    expect(screen.getByText("TMR")).toBeInTheDocument();
  });

  it("disables the NOW button when date is today", () => {
    const mockSetDate = vi.fn();
    const today = DateTime.now();

    render(<TodayTomorrowSwitch date={today} setDate={mockSetDate} />);

    expect(screen.getByText("NOW").closest("button")).toBeDisabled();
    expect(screen.getByText("TMR").closest("button")).not.toBeDisabled();
  });

  it("disables the TMR button when date is tomorrow", () => {
    const mockSetDate = vi.fn();
    const tomorrow = DateTime.now().plus({ days: 1 });

    render(<TodayTomorrowSwitch date={tomorrow} setDate={mockSetDate} />);

    expect(screen.getByText("TMR").closest("button")).toBeDisabled();
    expect(screen.getByText("NOW").closest("button")).not.toBeDisabled();
  });

  it("clicking TMR updates the date to tomorrow", () => {
    const mockSetDate = vi.fn();
    const today = DateTime.now();

    render(<TodayTomorrowSwitch date={today} setDate={mockSetDate} />);

    const tmrButton = screen.getByText("TMR").closest("button")!;
    fireEvent.click(tmrButton);

    expect(mockSetDate).toHaveBeenCalledWith(today.plus({ day: 1 }));
  });

  it("clicking NOW updates the date to today", () => {
    const mockSetDate = vi.fn();
    const tomorrow = DateTime.now().plus({ days: 1 });

    render(<TodayTomorrowSwitch date={tomorrow} setDate={mockSetDate} />);

    const nowButton = screen.getByText("NOW").closest("button")!;
    fireEvent.click(nowButton);

    expect(mockSetDate).toHaveBeenCalledWith(tomorrow.plus({ day: -1 }));
  });
});
