import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import FireZoneUnitTabs from "@/components/report/FireZoneUnitTabs";
import { FireShape, FireShapeStatusDetail } from "@/api/fbaAPI";
import type { FireCentre } from "@/types/fireCentre";
import { DateTime } from "luxon";
import { AdvisoryStatus } from "@/utils/constants";
import { useFireCentreDetails } from "@/hooks/useFireCentreDetails";

// Mock calculateStatusColour
vi.mock("@/utils/calculateZoneStatus", () => ({
  calculateStatusColour: () => "#FF0000",
}));

vi.mock("@/hooks/useFireCentreDetails", () => ({
  useFireCentreDetails: vi.fn() as typeof useFireCentreDetails,
}));

const mockUseFireCentreDetails = vi.mocked(useFireCentreDetails);
mockUseFireCentreDetails.mockImplementation(
  (
    fireCentre: FireCentre | undefined,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    _forDate: DateTime,
  ): FireShapeStatusDetail[] => {
    if (!fireCentre) return [];
    return [
      {
        fire_shape_id: 1,
        fire_shape_name: "Zone-1",
        fire_centre_name: fireCentre.name,
        status: AdvisoryStatus.ADVISORY,
      },
      {
        fire_shape_id: 2,
        fire_shape_name: "Zone-2",
        fire_centre_name: fireCentre.name,
        status: AdvisoryStatus.WARNING,
      },
    ];
  },
);

describe("FireZoneUnitTabs", () => {
  const mockFireCentre: FireCentre = {
    id: 1,
    name: "Fire Center 1",
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
        selectedFireCentre={mockFireCentre}
        selectedFireZoneUnit={mockFireShape}
        setSelectedFireZoneUnit={setSelectedFireZoneUnit}
        date={DateTime.now()}
      >
        <div data-testid="child-content">Child Content</div>
      </FireZoneUnitTabs>,
    );

    expect(screen.getByTestId("zone-1-tab")).toBeInTheDocument();
    expect(screen.getByTestId("zone-2-tab")).toBeInTheDocument();
    expect(screen.getByTestId("child-content")).toBeInTheDocument();
  });

  it("calls setSelectedFireZoneUnit when a tab is clicked", () => {
    render(
      <FireZoneUnitTabs
        selectedFireCentre={mockFireCentre}
        selectedFireZoneUnit={mockFireShape}
        setSelectedFireZoneUnit={setSelectedFireZoneUnit}
        date={DateTime.now()}
      >
        <div />
      </FireZoneUnitTabs>,
    );

    const tab = screen.getByTestId("zone-2-tab");
    fireEvent.click(tab);

    expect(setSelectedFireZoneUnit).toHaveBeenCalledWith({
      fire_shape_id: 2,
      mof_fire_centre_name: "Fire Center 1",
      mof_fire_zone_name: "Zone-2",
    });
  });
});
