import ScaleContainer from "@/components/ScaleContainer";
import { render, screen, act } from "@testing-library/react";
import { vi } from "vitest";

describe("ScaleContainer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it("renders the ScaleContainer when visible is true", () => {
    const setVisible = vi.fn();
    render(<ScaleContainer visible={true} timeout={3000} setVisible={setVisible} />);
    expect(screen.getByTestId("scale-container")).toBeInTheDocument();
  });

  it("calls setVisible(false) after the specified timeout", () => {
    const setVisible = vi.fn();
    render(<ScaleContainer visible={true} timeout={3000} setVisible={setVisible} />);
    act(() => {
      vi.advanceTimersByTime(3000);
    });
    expect(setVisible).toHaveBeenCalledWith(false);
  });

  it("does not call setVisible if visible is false", () => {
    const setVisible = vi.fn();
    render(<ScaleContainer visible={false} timeout={3000} setVisible={setVisible} />);
    act(() => {
      vi.advanceTimersByTime(3000);
    });
    expect(setVisible).not.toHaveBeenCalled();
  });
});
