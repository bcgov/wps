import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { DateTime } from "luxon";
import { describe, expect, it, vi, beforeEach } from "vitest";
import ASAGoMap, { ASAGoMapProps } from "@/components/map/ASAGoMap";
import { createTestStore } from "@/testUtils";
import { geolocationInitialState } from "@/slices/geolocationSlice";
import { RunType } from "@/api/fbaAPI";

class ResizeObserver {
  observe() {
    // mock no-op
  }
  unobserve() {
    // mock no-op
  }
  disconnect() {
    // mock no-op
  }
}

describe("ASAGoMap", () => {
  beforeAll(() => {
    window.ResizeObserver = ResizeObserver;
  });

  const defaultProps: ASAGoMapProps = {
    testId: "asa-go-map",
    selectedFireShape: undefined,
    setSelectedFireShape: vi.fn(),
    advisoryThreshold: 0,
    date: DateTime.now(),
    setDate: vi.fn(),
    setTab: vi.fn(),
    runType: RunType.FORECAST,
    runDatetime: DateTime.now(),
  };

  const mockPosition = {
    coords: {
      latitude: 49.2827,
      longitude: -123.1207,
      accuracy: 10,
      altitude: null,
      altitudeAccuracy: null,
      heading: null,
      speed: null,
    },
    timestamp: Date.now(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render the map", () => {
    const store = createTestStore();
    const { getByTestId } = render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    const mobileMap = getByTestId(defaultProps.testId);
    expect(mobileMap).toBeVisible();
  });

  it("renders the location button and location indicator", () => {
    const store = createTestStore({
      geolocation: {
        ...geolocationInitialState,
        position: mockPosition,
      },
    });

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    const locationButton = screen.getByTestId("location-button");
    const locationIndicator = screen.getByTestId("user-location-indicator");
    expect(locationIndicator).toBeInTheDocument();
    expect(locationButton).toBeInTheDocument();
    expect(locationButton).not.toBeDisabled();
  });
});
