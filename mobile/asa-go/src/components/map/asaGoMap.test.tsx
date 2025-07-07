import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { DateTime } from "luxon";
import { describe, expect, it, vi, beforeEach } from "vitest";
import ASAGoMap from "@/components/map/ASAGoMap";
import { createTestStore } from "@/testUtils";
import { geolocationInitialState } from "@/slices/geolocationSlice";

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

  const defaultProps = {
    selectedFireCenter: undefined,
    selectedFireShape: undefined,
    fireShapeAreas: [],
    advisoryThreshold: 0,
    date: DateTime.now(),
    setDate: vi.fn(),
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

    const mobileMap = getByTestId("fba-map");
    expect(mobileMap).toBeVisible();
  });

  it("renders the location button", () => {
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
    expect(locationButton).toBeInTheDocument();
    expect(locationButton).not.toBeDisabled();
  });
});
