import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { DateTime } from "luxon";
import Profile, { ProfileProps } from "@/components/profile/Profile";
import { FireCenter, FireShape } from "@/api/fbaAPI";

// Mock child components
vi.mock("@/components/FireCenterDropdown", () => ({
  default: ({
    selectedFireCenter,
  }: {
    selectedFireCenter: FireCenter | undefined;
  }) => (
    <div data-testid="fire-center-dropdown">
      {selectedFireCenter ? selectedFireCenter.name : "No fire center selected"}
    </div>
  ),
}));

vi.mock("@/components/profile/FireZoneUnitSummary", () => ({
  default: ({
    selectedFireZoneUnit,
  }: {
    selectedFireZoneUnit: FireShape | undefined;
  }) => (
    <div data-testid="fire-zone-unit-summary">
      {selectedFireZoneUnit
        ? `Summary for ${selectedFireZoneUnit.mof_fire_zone_name}`
        : "No fire zone selected"}
    </div>
  ),
}));

vi.mock("@/components/report/FireZoneUnitTabs", () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="fire-zone-unit-tabs">{children}</div>
  ),
}));

vi.mock("@/components/TodayTomorrowSwitch", () => ({
  default: ({ date }: { date: DateTime }) => (
    <div data-testid="today-tomorrow-switch">{date.toISODate()}</div>
  ),
}));

// Mock theme constants
vi.mock("@/theme", () => ({
  HEADER_GREY: "#f5f5f5",
  INFO_PANEL_CONTENT_BACKGROUND: "#ffffff",
}));

// Mock theme
vi.mock("@mui/material/styles", () => ({
  useTheme: () => ({
    spacing: (value: number) => `${value * 8}px`,
  }),
}));

describe("Profile", () => {
  const mockDate = DateTime.fromISO("2023-06-15");
  const mockSetDate = vi.fn();
  const mockSetSelectedFireCenter = vi.fn();
  const mockSetSelectedFireZoneUnit = vi.fn();

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

  const mockFireCenters = [mockFireCenter];

  const createMockStore = (fireCenters = mockFireCenters) => {
    return configureStore({
      reducer: {
        fireCenters: (state = { fireCenters }) => state,
      },
      preloadedState: {
        fireCenters: { fireCenters },
      },
    });
  };

  const renderWithProvider = (
    component: React.ReactElement,
    store = createMockStore(),
  ) => {
    return render(<Provider store={store}>{component}</Provider>);
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock useSelector to return fire centers
    vi.doMock("react-redux", async () => {
      const actual = await vi.importActual("react-redux");
      return {
        ...actual,
        useSelector: vi.fn(() => ({ fireCenters: mockFireCenters })),
      };
    });
  });

  const defaultProps: ProfileProps = {
    date: mockDate,
    setDate: mockSetDate,
    selectedFireCenter: undefined,
    setSelectedFireCenter: mockSetSelectedFireCenter,
    selectedFireZoneUnit: undefined,
    setSelectedFireZoneUnit: mockSetSelectedFireZoneUnit,
  };

  it("should render the Profile component", () => {
    renderWithProvider(<Profile {...defaultProps} />);

    expect(screen.getByTestId("asa-go-profile")).toBeInTheDocument();
  });

  it("should render TodayTomorrowSwitch with correct date", () => {
    renderWithProvider(<Profile {...defaultProps} />);

    const todayTomorrowSwitch = screen.getByTestId("today-tomorrow-switch");
    expect(todayTomorrowSwitch).toBeInTheDocument();
    expect(todayTomorrowSwitch).toHaveTextContent("2023-06-15");
  });

  it("should render FireCenterDropdown", () => {
    renderWithProvider(<Profile {...defaultProps} />);

    const dropdown = screen.getByTestId("fire-center-dropdown");
    expect(dropdown).toBeInTheDocument();
    expect(dropdown).toHaveTextContent("No fire center selected");
  });

  it("should render FireCenterDropdown with selected fire center", () => {
    const propsWithFireCenter = {
      ...defaultProps,
      selectedFireCenter: mockFireCenter,
    };

    renderWithProvider(<Profile {...propsWithFireCenter} />);

    const dropdown = screen.getByTestId("fire-center-dropdown");
    expect(dropdown).toHaveTextContent("Test Fire Center");
  });

  it("should render FireZoneUnitTabs", () => {
    renderWithProvider(
      <Profile {...defaultProps} selectedFireCenter={mockFireCenter} />,
    );

    const tabs = screen.getByTestId("fire-zone-unit-tabs");
    expect(tabs).toBeInTheDocument();
  });

  it("should render a default message if no fire centre is selected", () => {
    renderWithProvider(<Profile {...defaultProps} />);

    const summary = screen.getByTestId("default-message");
    expect(summary).toBeInTheDocument();
  });

  it("should render FireZoneUnitSummary with selected fire zone", () => {
    const propsWithFireZone = {
      ...defaultProps,
      selectedFireCenter: mockFireCenter,
      selectedFireZoneUnit: mockFireZoneUnit,
    };

    renderWithProvider(<Profile {...propsWithFireZone} />);

    const summary = screen.getByTestId("fire-zone-unit-summary");
    expect(summary).toHaveTextContent("Summary for Test Zone");
  });

  it("should have correct layout structure", () => {
    renderWithProvider(<Profile {...defaultProps} />);

    const profile = screen.getByTestId("asa-go-profile");
    expect(profile).toHaveStyle({
      display: "flex",
      flex: "1",
      flexDirection: "column",
      height: "100%",
      overflowY: "hidden",
    });

    const controlContainer = screen.getByTestId("profile-control-container");
    expect(controlContainer).toBeInTheDocument();
  });

  it("should have correct content container ID", () => {
    renderWithProvider(<Profile {...defaultProps} />);

    const contentContainer = document.getElementById(
      "profile-content-container",
    );
    expect(contentContainer).toBeInTheDocument();
  });

  it("should pass all props correctly to child components", () => {
    const propsWithAllValues: ProfileProps = {
      date: mockDate,
      setDate: mockSetDate,
      selectedFireCenter: mockFireCenter,
      setSelectedFireCenter: mockSetSelectedFireCenter,
      selectedFireZoneUnit: mockFireZoneUnit,
      setSelectedFireZoneUnit: mockSetSelectedFireZoneUnit,
    };

    renderWithProvider(<Profile {...propsWithAllValues} />);

    // Check that fire center is passed
    expect(screen.getByTestId("fire-center-dropdown")).toHaveTextContent(
      "Test Fire Center",
    );

    // Check that fire zone unit is passed
    expect(screen.getByTestId("fire-zone-unit-summary")).toHaveTextContent(
      "Summary for Test Zone",
    );
  });
});
