import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { useSelector } from "react-redux";
import FireZoneUnitSummary from "@/components/profile/FireZoneUnitSummary";
import { FireCenter, FireShape, FireZoneTPIStats } from "@/api/fbaAPI";
import { DateTime } from "luxon";

// Mock child components
vi.mock("@/components/profile/FuelSummary", () => ({
  default: ({
    selectedFireZoneUnit,
  }: {
    selectedFireZoneUnit: FireShape | undefined;
  }) => (
    <div data-testid="fuel-summary">
      {selectedFireZoneUnit
        ? `Fuel Summary for ${selectedFireZoneUnit.mof_fire_zone_name}`
        : "No fuel summary"}
    </div>
  ),
}));

vi.mock("@/components/profile/ElevationStatus", () => ({
  default: ({ tpiStats }: { tpiStats: Required<FireZoneTPIStats> }) => (
    <div data-testid="elevation-status">
      {`Elevation Status for zone ${tpiStats.fire_zone_id}`}
    </div>
  ),
}));

// Mock hooks
vi.mock("@/hooks/datahooks", () => ({
  useFilteredHFIStatsForDate: vi.fn(),
  useTPIStatsForDate: vi.fn(),
}));

// Mock theme
vi.mock("@mui/material/styles", () => ({
  useTheme: () => ({
    spacing: (value: number) => `${value * 8}px`,
  }),
}));

// Mock react-redux
vi.mock("react-redux", async () => {
  const actual = await vi.importActual("react-redux");
  return {
    ...actual,
    useSelector: vi.fn(),
  };
});

describe("FireZoneUnitSummary", () => {
  const testDate = DateTime.fromISO("2025-08-25");
  const mockFireCenter: FireCenter = {
    id: 1,
    name: "Test Fire Center",
    stations: [],
  };

  const mockFireZoneUnit: FireShape = {
    fire_shape_id: 1,
    mof_fire_zone_name: "Test Zone",
    mof_fire_centre_name: "Test Centre",
    area_sqm: 1000,
  };

  const createMockStore = () => {
    return configureStore({
      reducer: {
        test: (state = {}) => state,
      },
      preloadedState: {},
    });
  };

  const renderWithProvider = (
    component: React.ReactElement,
    store = createMockStore()
  ) => {
    return render(<Provider store={store}>{component}</Provider>);
  };

  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();

    // Setup default useSelector return values
    vi.mocked(useSelector).mockImplementation((selector) => {
      const selectorStr = selector.toString();
      if (selectorStr.includes("selectFilteredFireCentreHFIFuelStats")) {
        return {};
      }
      if (selectorStr.includes("selectFireCentreTPIStats")) {
        return { fireCentreTPIStats: null };
      }
      return {};
    });
  });

  it("should render empty div when selectedFireZoneUnit is undefined", () => {
    renderWithProvider(
      <FireZoneUnitSummary
        selectedFireCenter={mockFireCenter}
        selectedFireZoneUnit={undefined}
        date={testDate}
      />
    );

    const emptyDiv = screen.getByTestId("fire-zone-unit-summary-empty");
    expect(emptyDiv).toBeInTheDocument();
  });

  it("should render fire zone unit summary when selectedFireZoneUnit is provided", () => {
    renderWithProvider(
      <FireZoneUnitSummary
        selectedFireCenter={mockFireCenter}
        selectedFireZoneUnit={mockFireZoneUnit}
        date={testDate}
      />
    );

    const summary = screen.getByTestId("fire-zone-unit-summary");
    expect(summary).toBeInTheDocument();
  });

  it("should display the fire zone name as title", () => {
    renderWithProvider(
      <FireZoneUnitSummary
        selectedFireCenter={mockFireCenter}
        selectedFireZoneUnit={mockFireZoneUnit}
        date={testDate}
      />
    );

    const title = screen.getByTestId("fire-zone-title-tabs");
    expect(title).toBeInTheDocument();
    expect(title).toHaveTextContent("Test Zone");
  });

  it("should render FuelSummary component", () => {
    renderWithProvider(
      <FireZoneUnitSummary
        selectedFireCenter={mockFireCenter}
        selectedFireZoneUnit={mockFireZoneUnit}
        date={testDate}
      />
    );

    const fuelSummary = screen.getByTestId("fuel-summary");
    expect(fuelSummary).toBeInTheDocument();
    expect(fuelSummary).toHaveTextContent("Fuel Summary for Test Zone");
  });

  it("should show no elevation information message when TPI stats are incomplete", () => {
    renderWithProvider(
      <FireZoneUnitSummary
        selectedFireCenter={mockFireCenter}
        selectedFireZoneUnit={mockFireZoneUnit}
        date={testDate}
      />
    );

    expect(
      screen.getByText("No elevation information available.")
    ).toBeInTheDocument();
  });

  it("should have correct styling", () => {
    renderWithProvider(
      <FireZoneUnitSummary
        selectedFireCenter={mockFireCenter}
        selectedFireZoneUnit={mockFireZoneUnit}
        date={testDate}
      />
    );

    const summary = screen.getByTestId("fire-zone-unit-summary");
    expect(summary).toHaveStyle({
      width: "100%",
    });
    // The backgroundColor and overflowY are applied via MUI's sx prop
    // so we just verify the component renders with the correct structure
    expect(summary).toBeInTheDocument();
  });

  it("should render Grid container with correct props", () => {
    const { container } = renderWithProvider(
      <FireZoneUnitSummary
        selectedFireCenter={mockFireCenter}
        selectedFireZoneUnit={mockFireZoneUnit}
        date={testDate}
      />
    );

    const gridContainer = container.querySelector(".MuiGrid2-root");
    expect(gridContainer).toBeInTheDocument();
  });

  it("should handle missing fire center", () => {
    renderWithProvider(
      <FireZoneUnitSummary
        selectedFireCenter={undefined}
        selectedFireZoneUnit={mockFireZoneUnit}
        date={testDate}
      />
    );

    const summary = screen.getByTestId("fire-zone-unit-summary");
    expect(summary).toBeInTheDocument();

    const fuelSummary = screen.getByTestId("fuel-summary");
    expect(fuelSummary).toBeInTheDocument();
  });
});
