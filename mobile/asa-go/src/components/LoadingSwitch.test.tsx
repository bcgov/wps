import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import LoadingSwitch from "./LoadingSwitch";

describe("LoadingSwitch", () => {
  it("renders as unchecked", () => {
    render(
      <LoadingSwitch checked={false} onChange={vi.fn()} aria-label="test" />,
    );
    expect(screen.getByRole("checkbox")).not.toBeChecked();
  });

  it("renders as checked", () => {
    render(
      <LoadingSwitch checked={true} onChange={vi.fn()} aria-label="test" />,
    );
    expect(screen.getByRole("checkbox")).toBeChecked();
  });

  it("calls onChange when clicked", () => {
    const onChange = vi.fn();
    render(
      <LoadingSwitch checked={false} onChange={onChange} aria-label="test" />,
    );
    fireEvent.click(screen.getByRole("checkbox"));
    expect(onChange).toHaveBeenCalled();
  });

  it("disables the switch while loading", () => {
    render(
      <LoadingSwitch
        checked={false}
        onChange={vi.fn()}
        aria-label="test"
        loading
      />,
    );
    expect(screen.getByRole("checkbox")).toBeDisabled();
  });

  it("disables the switch when disabled", () => {
    render(
      <LoadingSwitch
        checked={false}
        onChange={vi.fn()}
        aria-label="test"
        disabled
      />,
    );
    expect(screen.getByRole("checkbox")).toBeDisabled();
  });

  it("shows error text when error is provided", () => {
    render(
      <LoadingSwitch
        checked={false}
        onChange={vi.fn()}
        aria-label="test"
        error="something went wrong, please try again"
      />,
    );
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    expect(screen.queryAllByTestId("loading-switch-error").length === 1);
  });

  it("does not show error text when error is not provided", () => {
    render(
      <LoadingSwitch checked={false} onChange={vi.fn()} aria-label="test" />,
    );
    expect(screen.queryByText(/something went wrong/i)).not.toBeInTheDocument();
    expect(screen.queryAllByTestId("loading-switch-error").length === 0);
  });

  it("does not call onChange while loading", async () => {
    const user = userEvent.setup({ pointerEventsCheck: 0 });
    const onChange = vi.fn();
    render(
      <LoadingSwitch
        checked={false}
        onChange={onChange}
        aria-label="test"
        loading
      />,
    );
    await user.click(screen.getByRole("checkbox"));
    expect(onChange).not.toHaveBeenCalled();
  });
});
