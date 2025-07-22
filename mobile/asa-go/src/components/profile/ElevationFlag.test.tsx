import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ElevationFlag from "@/components/profile/ElevationFlag";

// Mock the FillableFlag component to test integration
vi.mock("@/components/profile/FillableFlag", () => ({
  default: ({
    maskId,
    percent,
    testId,
  }: {
    maskId: string;
    percent: number;
    testId?: string;
  }) => (
    <div
      data-testid={`mock-flag-${maskId}`}
      data-percent={percent}
      data-test-id={testId}
    >
      Mock Flag: {percent}%
    </div>
  ),
}));

describe("ElevationFlag", () => {
  it("should render the flag component", () => {
    render(<ElevationFlag id="upper" percent={75} testId="upper-slope" />);

    const mockFlag = screen.getByTestId("mock-flag-upper");
    expect(mockFlag).toBeInTheDocument();
  });

  it("should pass correct props to FillableFlag", () => {
    render(<ElevationFlag id="test-id" percent={50} testId="test-flag" />);

    const mockFlag = screen.getByTestId("mock-flag-test-id");
    expect(mockFlag).toHaveAttribute("data-percent", "50");
    expect(mockFlag).toHaveAttribute("data-test-id", "test-flag");
  });

  it("should pass maskId prop correctly", () => {
    const testIds = ["upper", "mid", "lower"];

    testIds.forEach((id) => {
      const { container } = render(<ElevationFlag id={id} percent={25} />);
      const mockFlag = container.querySelector(
        `[data-testid="mock-flag-${id}"]`
      );
      expect(mockFlag).toBeInTheDocument();
    });
  });

  it("should have correct Grid styling", () => {
    const { container } = render(<ElevationFlag id="test" percent={50} />);

    // The Grid should have specific styling
    const gridElement = container.firstChild;
    expect(gridElement).toHaveClass("MuiGrid2-root");
  });

  it("should handle different percentage values", () => {
    const percentages = [0, 25, 50, 75, 100];

    percentages.forEach((percent) => {
      const { container } = render(
        <ElevationFlag id="test" percent={percent} />
      );
      const mockFlag = container.querySelector(
        '[data-testid="mock-flag-test"]'
      );
      expect(mockFlag).toHaveAttribute("data-percent", percent.toString());
    });
  });
});
