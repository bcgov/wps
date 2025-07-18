import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import Advisory from "@/components/report/Advisory";
import { DateTime } from "luxon";
import React from "react";
import { useSelector } from "react-redux";
import { FireCenter, FireShape } from "@/api/fbaAPI";

// Mock child components with proper props
vi.mock("@/components/TodayTomorrowSwitch", () => ({
  default: ({ date }: { date: DateTime }) => (
    <div data-testid="today-tomorrow-switch">Date: {date.toISODate()}</div>
  ),
}));

vi.mock("@/components/FireCenterDropdown", () => ({
  default: ({
    fireCenterOptions,
  }: {
    fireCenterOptions: FireCenter[];
    selectedFireCenter: FireCenter | undefined;
    setSelectedFireCenter: React.Dispatch<React.SetStateAction<FireCenter | undefined>>;
    setSelectedFireShape: React.Dispatch<React.SetStateAction<FireShape | undefined>>;
  }) => (
    <div data-testid="fire-center-dropdown">Options: {fireCenterOptions.length}</div>
  ),
}));

vi.mock("@/components/report/FireZoneUnitTabs", () => ({
  default: ({
    children,
  }: {
    advisoryThreshold: number;
    selectedFireCenter: FireCenter | undefined;
    selectedFireZoneUnit: FireShape | undefined;
    setSelectedFireZoneUnit: React.Dispatch<React.SetStateAction<FireShape | undefined>>;
    children: React.ReactNode;
  }) => <div data-testid="fire-zone-tabs">{children}</div>,
}));

vi.mock("@/components/report/AdvisoryText", () => ({
  default: ({
    advisoryThreshold,
    selectedFireCenter,
    selectedFireZoneUnit,
  }: {
    advisoryThreshold: number;
    selectedFireCenter: FireCenter | undefined;
    selectedFireZoneUnit: FireShape | undefined;
  }) => <div data-testid="advisory-text">Advisory Text Content</div>,
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
  const mockFireCenters: FireCenter[] = [
    { name: "Center 1", id: 1, stations: [] },
    { name: "Center 2", id: 2, stations: [] },
  ];

  const mockDate: DateTime = DateTime.fromISO("2025-07-15");

  const setDate = vi.fn();
  const setSelectedFireCenter = vi.fn();
  const setSelectedFireZoneUnit = vi.fn();

  beforeEach(() => {
    (useSelector as vi.Mock).mockReturnValue({ fireCenters: mockFireCenters });
  });

  it("renders all key sections and child components", () => {
    render(
      <Advisory
        advisoryThreshold={5}
        date={mockDate}
        setDate={setDate}
        selectedFireCenter={undefined}
        setSelectedFireCenter={setSelectedFireCenter}
        selectedFireZoneUnit={undefined}
        setSelectedFireZoneUnit={setSelectedFireZoneUnit}
      />
    );

    expect(screen.getByTestId("asa-go-advisory")).toBeInTheDocument();
    expect(screen.getByTestId("advisory-control-container")).toBeInTheDocument();
    expect(screen.getByTestId("today-tomorrow-switch")).toHaveTextContent("2025-07-15");
    expect(screen.getByTestId("fire-center-dropdown")).toHaveTextContent("Options: 2");
    expect(screen.getByText("Advisory Report")).toBeInTheDocument();
    expect(screen.getByTestId("fire-zone-tabs")).toBeInTheDocument();
    expect(screen.getByTestId("advisory-text")).toHaveTextContent("Advisory Text Content");
  });
});
