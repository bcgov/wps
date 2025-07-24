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
    const { container } = render(
      <ElevationFlag percent={75} testId="upper-slope" />
    );

    const mockFlag = container.querySelector('[data-percent="75"]');
    expect(mockFlag).toBeInTheDocument();
    expect(mockFlag).toHaveAttribute("data-test-id", "upper-slope");
  });

  it("should pass correct props to FillableFlag", () => {
    render(<ElevationFlag percent={50} testId="test-flag" />);

    const mockFlag = screen.getByText(/Mock Flag: 50%/);
    expect(mockFlag).toHaveAttribute("data-percent", "50");
    expect(mockFlag).toHaveAttribute("data-test-id", "test-flag");
  });

  it("should generate random maskId correctly", () => {
    const { container: container1 } = render(<ElevationFlag percent={25} />);
    const { container: container2 } = render(<ElevationFlag percent={25} />);

    // Both should have mock flags with different maskIds since they're random
    const mockFlag1 = container1.querySelector(
      '[data-testid^="mock-flag-elevation-flag-"]'
    );
    const mockFlag2 = container2.querySelector(
      '[data-testid^="mock-flag-elevation-flag-"]'
    );

    expect(mockFlag1).toBeInTheDocument();
    expect(mockFlag2).toBeInTheDocument();

    // The maskIds should be different (random)
    const maskId1 = mockFlag1?.getAttribute("data-testid");
    const maskId2 = mockFlag2?.getAttribute("data-testid");
    expect(maskId1).not.toBe(maskId2);
  });

  it("should have correct Grid styling", () => {
    const { container } = render(<ElevationFlag percent={50} />);

    // The Grid should have specific styling
    const gridElement = container.firstChild;
    expect(gridElement).toHaveClass("MuiGrid2-root");
  });

  it("should handle different percentage values", () => {
    const percentages = [0, 25, 50, 75, 100];

    percentages.forEach((percent) => {
      const { container } = render(
        <ElevationFlag testId="test" percent={percent} />
      );
      // Since maskId is now random, we need to find the element differently
      const mockFlag = container.querySelector(
        '[data-testid^="mock-flag-elevation-flag-"]'
      );
      expect(mockFlag).toBeInTheDocument();
      expect(mockFlag).toHaveAttribute("data-percent", percent.toString());
    });
  });
});
