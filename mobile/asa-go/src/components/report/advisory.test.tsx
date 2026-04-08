import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import Advisory from "@/components/report/Advisory";
import { DateTime } from "luxon";
import { useSelector } from "react-redux";
import type { FireCentre } from "@/types/fireCentre";
import { AdvisoryTextProps } from "@/components/report/AdvisoryText";
import { FireZoneUnitTabsProps } from "@/components/report/FireZoneUnitTabs";
import { FireCenterDropdownProps } from "@/components/FireCenterDropdown";

// Mock child components with proper props
vi.mock("@/components/TodayTomorrowSwitch", () => ({
  default: ({ date }: { date: DateTime }) => (
    <div data-testid="today-tomorrow-switch">Date: {date.toISODate()}</div>
  ),
}));

vi.mock("@/components/FireCenterDropdown", () => ({
  default: ({ fireCentreOptions }: FireCenterDropdownProps) => (
    <div data-testid="fire-center-dropdown">
      Options: {fireCentreOptions.length}
    </div>
  ),
}));

vi.mock("@/components/report/FireZoneUnitTabs", () => ({
  default: ({ children }: FireZoneUnitTabsProps) => (
    <div data-testid="fire-zone-tabs">{children}</div>
  ),
}));

vi.mock("@/components/report/AdvisoryText", () => ({
  AdvisoryTypography: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  default: (_: AdvisoryTextProps) => (
    <div data-testid="advisory-text">Advisory Text Content</div>
  ),
}));

// Mock Redux selector
vi.mock("react-redux", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-redux")>();
  return {
    ...actual,
    useSelector: vi.fn(),
  };
});

describe("Advisory Component", () => {
  const mockFireCentres: FireCentre[] = [
    { name: "Center 1", id: 1 },
    { name: "Center 2", id: 2 },
  ];

  const mockDate: DateTime = DateTime.fromISO("2025-07-15");

  const setDate = vi.fn();
  const setSelectedFireCentre = vi.fn();
  const setSelectedFireZoneUnit = vi.fn();

  beforeEach(() => {
    vi.mocked(useSelector).mockReturnValue({ fireCentres: mockFireCentres });
  });

  it("renders all key sections and child components", () => {
    render(
      <Advisory
        date={mockDate}
        setDate={setDate}
        selectedFireCentre={mockFireCentres[0]}
        setSelectedFireCentre={setSelectedFireCentre}
        selectedFireZoneUnit={undefined}
        setSelectedFireZoneUnit={setSelectedFireZoneUnit}
      />,
    );

    expect(screen.getByTestId("asa-go-advisory")).toBeInTheDocument();
    expect(
      screen.getByTestId("advisory-control-container"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("today-tomorrow-switch")).toHaveTextContent(
      "2025-07-15",
    );
    expect(screen.getByTestId("fire-center-dropdown")).toHaveTextContent(
      "Options: 2",
    );
    expect(screen.getByTestId("fire-zone-tabs")).toBeInTheDocument();
    expect(screen.getByTestId("advisory-text")).toHaveTextContent(
      "Advisory Text Content",
    );
  });
});
