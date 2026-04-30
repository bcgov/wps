import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import FuelSummary from "@/components/profile/FuelSummary";
import { FireShape, FireZoneFuelStats } from "@/api/fbaAPI";

// Mock MUI DataGrid Pro to avoid ES module resolution issues
vi.mock("@mui/x-data-grid-pro", () => ({
  DataGridPro: ({ rows, columns }: { rows: unknown[]; columns: unknown[] }) => (
    <div data-testid="data-grid-pro" role="grid">
      <div data-testid="grid-rows">{rows.length} rows</div>
      <div data-testid="grid-columns">{columns.length} columns</div>
      {rows.map((row, index) => {
        const rowData = row as Record<string, unknown>;
        return (
          <div
            key={(rowData.id as string) || index}
            data-testid={`grid-row-${index}`}
          >
            {rowData.fuelTypeCode as string} - {rowData.area as number}
          </div>
        );
      })}
    </div>
  ),
  GridColDef: {},
}));

// Mock the child components
vi.mock("@/components/profile/FuelDistribution", () => ({
  default: ({ code, percent }: { code: string; percent: number }) => (
    <div data-testid={`fuel-distribution-${code}`} data-percent={percent}>
      Fuel Distribution: {code} - {percent}%
    </div>
  ),
}));

vi.mock("@/components/profile/CriticalHours", () => ({
  default: ({ start, end }: { start?: number; end?: number }) => (
    <div data-testid="critical-hours">
      {start !== undefined && end !== undefined
        ? `${start}:00 - ${end}:00`
        : "-"}
    </div>
  ),
}));

describe("FuelSummary", () => {
  const mockFireShape: FireShape = {
    fire_shape_id: 1,
    mof_fire_zone_name: "Test Zone",
    mof_fire_centre_name: "Test Centre",
    area_sqm: 1000,
  };

  const mockFuelStats: FireZoneFuelStats[] = [
    {
      fuel_type: {
        fuel_type_id: 1,
        fuel_type_code: "C-1",
        description: "Spruce-Lichen Woodland",
      },
      threshold: {
        id: 1,
        name: "advisory",
        description: "4000 < hfi < 10000",
      },
      critical_hours: {
        start_time: 10,
        end_time: 18,
      },
      area: 500,
      fuel_area: 1000,
    },
    {
      fuel_type: {
        fuel_type_id: 2,
        fuel_type_code: "C-2",
        description: "Boreal Spruce",
      },
      threshold: {
        id: 1,
        name: "advisory",
        description: "4000 < hfi < 10000",
      },
      critical_hours: {
        start_time: 12,
        end_time: 16,
      },
      area: 300,
      fuel_area: 800,
    },
  ];

  const mockFireZoneFuelStats = {
    1: mockFuelStats,
  };

  it("should render the DataGridPro when fuel data is available", () => {
    render(
      <FuelSummary
        fireZoneFuelStats={mockFireZoneFuelStats}
        selectedFireZoneUnit={mockFireShape}
      />
    );

    // Check that our mocked DataGrid is rendered
    expect(screen.getByTestId("data-grid-pro")).toBeInTheDocument();
    expect(screen.getByRole("grid")).toBeInTheDocument();

    // Check that no data message is not shown
    expect(
      screen.queryByText("No fuel type information available.")
    ).not.toBeInTheDocument();
  });

  it("should show no data message when fuel stats are empty", () => {
    render(
      <FuelSummary
        fireZoneFuelStats={{}}
        selectedFireZoneUnit={mockFireShape}
      />
    );

    expect(
      screen.getByText("No fuel type information available.")
    ).toBeInTheDocument();
  });

  it("should show no data message when selectedFireZoneUnit is undefined", () => {
    render(
      <FuelSummary
        fireZoneFuelStats={mockFireZoneFuelStats}
        selectedFireZoneUnit={undefined}
      />
    );

    expect(
      screen.getByText("No fuel type information available.")
    ).toBeInTheDocument();
  });

  it("should show no data message when fireZoneFuelStats is undefined", () => {
    render(
      <FuelSummary
        fireZoneFuelStats={
          undefined as unknown as Record<number, FireZoneFuelStats[]>
        }
        selectedFireZoneUnit={mockFireShape}
      />
    );

    expect(
      screen.getByText("No fuel type information available.")
    ).toBeInTheDocument();
  });

  it("should show no data message when fuel details for selected zone are not available", () => {
    const emptyFireZoneFuelStats = {
      2: mockFuelStats, // Different fire_shape_id
    };

    render(
      <FuelSummary
        fireZoneFuelStats={emptyFireZoneFuelStats}
        selectedFireZoneUnit={mockFireShape}
      />
    );

    expect(
      screen.getByText("No fuel type information available.")
    ).toBeInTheDocument();
  });

  it("should handle empty fuel details array", () => {
    const emptyFireZoneFuelStats = {
      1: [],
    };

    render(
      <FuelSummary
        fireZoneFuelStats={emptyFireZoneFuelStats}
        selectedFireZoneUnit={mockFireShape}
      />
    );

    expect(
      screen.getByText("No fuel type information available.")
    ).toBeInTheDocument();
  });

  it("should process fuel data correctly with different fire_shape_ids", () => {
    const differentShapeFireStats = {
      1: mockFuelStats,
      2: [
        {
          fuel_type: {
            fuel_type_id: 3,
            fuel_type_code: "S-1",
            description: "Slash",
          },
          threshold: {
            id: 1,
            name: "advisory",
            description: "4000 < hfi < 10000",
          },
          critical_hours: {
            start_time: 8,
            end_time: 20,
          },
          area: 200,
          fuel_area: 500,
        },
      ],
    };

    const differentFireShape: FireShape = {
      fire_shape_id: 2,
      mof_fire_zone_name: "Different Zone",
      mof_fire_centre_name: "Different Centre",
      area_sqm: 2000,
    };

    render(
      <FuelSummary
        fireZoneFuelStats={differentShapeFireStats}
        selectedFireZoneUnit={differentFireShape}
      />
    );

    // Should not show no data message for the different fire shape
    expect(
      screen.queryByText("No fuel type information available.")
    ).not.toBeInTheDocument();
  });

  it("should render DataGrid with correct data structure", () => {
    render(
      <FuelSummary
        fireZoneFuelStats={mockFireZoneFuelStats}
        selectedFireZoneUnit={mockFireShape}
      />
    );

    const dataGrid = screen.getByTestId("data-grid-pro");
    expect(dataGrid).toBeInTheDocument();

    // Check that grid shows expected number of rows (2 fuel types)
    expect(screen.getByTestId("grid-rows")).toHaveTextContent("2 rows");

    // Check that grid shows columns
    const gridColumns = screen.getByTestId("grid-columns");
    expect(gridColumns).toBeInTheDocument();
  });

  it("should handle DataGrid with no data gracefully", () => {
    render(
      <FuelSummary
        fireZoneFuelStats={{}}
        selectedFireZoneUnit={mockFireShape}
      />
    );

    // Should show no data message instead of DataGrid
    expect(
      screen.getByText("No fuel type information available.")
    ).toBeInTheDocument();

    // DataGrid should not be rendered when there's no data
    expect(screen.queryByTestId("data-grid-pro")).not.toBeInTheDocument();
  });
});
