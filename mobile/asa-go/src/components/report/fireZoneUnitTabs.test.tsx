import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import FireZoneUnitTabs from "@/components/report/FireZoneUnitTabs";
import { FireCenter, FireShape } from "@/api/fbaAPI";
import { DateTime } from "luxon";

// Mock calculateStatusColour
vi.mock("@/utils/calculateZoneStatus", () => ({
  calculateStatusColour: () => "#FF0000",
}));

// Mock useFireCentreDetails
vi.mock("@/hooks/useFireCentreDetails", () => ({
  useFireCentreDetails: (fireCenter: FireCenter | undefined) => [
    {
      fire_shape_id: "zone-1",
      fire_shape_name: "Zone-1",
      fire_centre_name: fireCenter?.name ?? "Unknown",
      fireShapeDetails: [],
    },
    {
      fire_shape_id: "zone-2",
      fire_shape_name: "Zone-2",
      fire_centre_name: fireCenter?.name ?? "Unknown",
      fireShapeDetails: [],
    },
  ],
}));

describe("FireZoneUnitTabs", () => {
  const mockFireCenter: FireCenter = {
    id: 1,
    name: "Fire Center 1",
    stations: [],
  };

  const mockFireShape: FireShape = {
    fire_shape_id: 1,
    mof_fire_centre_name: "Fire Center 1",
    mof_fire_zone_name: "Zone-1",
  };

  const setSelectedFireZoneUnit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders tabs and children", () => {
    render(
      <FireZoneUnitTabs
        advisoryThreshold={5}
        selectedFireCenter={mockFireCenter}
        selectedFireZoneUnit={mockFireShape}
        setSelectedFireZoneUnit={setSelectedFireZoneUnit}
        date={DateTime.now()}
      >
        <div data-testid="child-content">Child Content</div>
      </FireZoneUnitTabs>
    );

    expect(screen.getByTestId("zone-zone-1-tab")).toBeInTheDocument();
    expect(screen.getByTestId("zone-zone-2-tab")).toBeInTheDocument();
    expect(screen.getByTestId("child-content")).toBeInTheDocument();
  });

  it("calls setSelectedFireZoneUnit when a tab is clicked", () => {
    render(
      <FireZoneUnitTabs
        advisoryThreshold={5}
        selectedFireCenter={mockFireCenter}
        selectedFireZoneUnit={mockFireShape}
        setSelectedFireZoneUnit={setSelectedFireZoneUnit}
        date={DateTime.now()}
      >
        <div />
      </FireZoneUnitTabs>
    );

    const tab = screen.getByTestId("zone-zone-2-tab");
    fireEvent.click(tab);

    expect(setSelectedFireZoneUnit).toHaveBeenCalledWith({
      fire_shape_id: "zone-2",
      mof_fire_centre_name: "Fire Center 1",
      mof_fire_zone_name: "Zone-2",
    });
  });
});
