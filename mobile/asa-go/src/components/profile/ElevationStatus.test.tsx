import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ElevationStatus from "@/components/profile/ElevationStatus";
import { FireZoneTPIStats } from "@/api/fbaAPI";

// Mock the child components
vi.mock("@/components/profile/ElevationLabel", () => ({
  default: ({ label }: { label: string }) => (
    <div
      data-testid={`elevation-label-${label.toLowerCase().replace(" ", "-")}`}
    >
      {label}
    </div>
  ),
}));

vi.mock("@/components/profile/ElevationFlag", () => ({
  default: ({
    id,
    percent,
    testId,
  }: {
    id: string;
    percent: number;
    testId?: string;
  }) => (
    <div data-testid={testId || `elevation-flag-${id}`} data-percent={percent}>
      Flag: {percent}%
    </div>
  ),
}));

describe("ElevationStatus", () => {
  const mockTpiStats: Required<FireZoneTPIStats> = {
    fire_zone_id: 1,
    valley_bottom_tpi: 100,
    valley_bottom_hfi: 25,
    mid_slope_tpi: 200,
    mid_slope_hfi: 100,
    upper_slope_tpi: 150,
    upper_slope_hfi: 75,
  };

  it("should render the elevation status component", () => {
    render(<ElevationStatus tpiStats={mockTpiStats} />);

    const elevationStatus = screen.getByTestId("elevation-status");
    expect(elevationStatus).toBeInTheDocument();
  });

  it("should render the mountain background", () => {
    render(<ElevationStatus tpiStats={mockTpiStats} />);

    const mountainElement = screen.getByTestId("tpi-mountain");
    expect(mountainElement).toBeInTheDocument();
  });

  it("should render all three elevation zones", () => {
    render(<ElevationStatus tpiStats={mockTpiStats} />);

    // Check for elevation labels
    expect(
      screen.getByTestId("elevation-label-upper-slope"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("elevation-label-mid-slope")).toBeInTheDocument();
    expect(
      screen.getByTestId("elevation-label-valley-bottom"),
    ).toBeInTheDocument();

    // Check for elevation flags
    expect(screen.getByTestId("upper-slope")).toBeInTheDocument();
    expect(screen.getByTestId("mid-slope")).toBeInTheDocument();
    expect(screen.getByTestId("valley-bottom")).toBeInTheDocument();
  });

  it("should calculate correct percentages for each elevation zone", () => {
    render(<ElevationStatus tpiStats={mockTpiStats} />);

    // Upper slope: 75/150 = 50%
    const upperSlope = screen.getByTestId("upper-slope");
    expect(upperSlope).toHaveAttribute("data-percent", "50");

    // Mid slope: 100/200 = 50%
    const midSlope = screen.getByTestId("mid-slope");
    expect(midSlope).toHaveAttribute("data-percent", "50");

    // Valley bottom: 25/100 = 25%
    const valleyBottom = screen.getByTestId("valley-bottom");
    expect(valleyBottom).toHaveAttribute("data-percent", "25");
  });

  it("should handle zero TPI values", () => {
    const zeroTpiStats: Required<FireZoneTPIStats> = {
      fire_zone_id: 1,
      valley_bottom_tpi: 0,
      valley_bottom_hfi: 0,
      mid_slope_tpi: 0,
      mid_slope_hfi: 0,
      upper_slope_tpi: 0,
      upper_slope_hfi: 0,
    };

    render(<ElevationStatus tpiStats={zeroTpiStats} />);

    // All percentages should be 0 when TPI is 0
    expect(screen.getByTestId("upper-slope")).toHaveAttribute(
      "data-percent",
      "0",
    );
    expect(screen.getByTestId("mid-slope")).toHaveAttribute(
      "data-percent",
      "0",
    );
    expect(screen.getByTestId("valley-bottom")).toHaveAttribute(
      "data-percent",
      "0",
    );
  });

  it("should handle mixed zero and non-zero values", () => {
    const mixedTpiStats: Required<FireZoneTPIStats> = {
      fire_zone_id: 1,
      valley_bottom_tpi: 0,
      valley_bottom_hfi: 10,
      mid_slope_tpi: 100,
      mid_slope_hfi: 50,
      upper_slope_tpi: 200,
      upper_slope_hfi: 0,
    };

    render(<ElevationStatus tpiStats={mixedTpiStats} />);

    // Valley bottom: TPI is 0, so percentage should be 0
    expect(screen.getByTestId("valley-bottom")).toHaveAttribute(
      "data-percent",
      "0",
    );

    // Mid slope: 50/100 = 50%
    expect(screen.getByTestId("mid-slope")).toHaveAttribute(
      "data-percent",
      "50",
    );

    // Upper slope: 0/200 = 0%
    expect(screen.getByTestId("upper-slope")).toHaveAttribute(
      "data-percent",
      "0",
    );
  });

  it("should round percentages correctly", () => {
    const fractionalTpiStats: Required<FireZoneTPIStats> = {
      fire_zone_id: 1,
      valley_bottom_tpi: 3,
      valley_bottom_hfi: 1, // 1/3 = 33.33... should round to 33
      mid_slope_tpi: 3,
      mid_slope_hfi: 2, // 2/3 = 66.66... should round to 67
      upper_slope_tpi: 7,
      upper_slope_hfi: 5, // 5/7 = 71.42... should round to 71
    };

    render(<ElevationStatus tpiStats={fractionalTpiStats} />);

    expect(screen.getByTestId("valley-bottom")).toHaveAttribute(
      "data-percent",
      "33",
    );
    expect(screen.getByTestId("mid-slope")).toHaveAttribute(
      "data-percent",
      "67",
    );
    expect(screen.getByTestId("upper-slope")).toHaveAttribute(
      "data-percent",
      "71",
    );
  });

  it("should render header text correctly", () => {
    render(<ElevationStatus tpiStats={mockTpiStats} />);

    expect(screen.getByText("Topographic Position:")).toBeInTheDocument();
    expect(
      screen.getByText("Proportion of Advisory Area:"),
    ).toBeInTheDocument();
  });

  it("should have proper styling and layout", () => {
    render(<ElevationStatus tpiStats={mockTpiStats} />);

    const elevationStatus = screen.getByTestId("elevation-status");
    expect(elevationStatus).toHaveClass("MuiGrid2-root");

    const mountainElement = screen.getByTestId("tpi-mountain");
    expect(mountainElement).toBeInTheDocument();
    // Mountain should have background image
    expect(mountainElement).toHaveStyle({ backgroundRepeat: "round" });
  });
});
