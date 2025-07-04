import { fireEvent, render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { DateTime } from "luxon";
import { describe, expect, it, vi, beforeEach } from "vitest";
import ASAGoMap from "@/components/map/ASAGoMap";
import { createTestStore } from "@/testUtils";
import { geolocationInitialState } from "@/slices/geolocationSlice";
import type * as GeolocationSlice from "@/slices/geolocationSlice";
import { AppDispatch } from "@/store";

global.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// mock the geolocation actions
const mockStartLocationTracking = vi.fn();
vi.mock("@/slices/geolocationSlice", async () => {
  const actual = await import("@/slices/geolocationSlice");
  return {
    ...(actual as typeof GeolocationSlice),
    startLocationTracking: (): ((dispatch: AppDispatch) => Promise<void>) => {
      return async () => {
        mockStartLocationTracking();
      };
    },
  };
});

describe("ASAGoMap", () => {
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

  it("starts location tracking on component mount", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    expect(mockStartLocationTracking).toHaveBeenCalledTimes(1);
  });

  it("enables location button when has position even if loading", () => {
    const store = createTestStore({
      geolocation: {
        ...geolocationInitialState,
        loading: true,
        position: mockPosition,
      },
    });

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    const locationButton = screen.getByTestId("location-button");
    expect(locationButton).not.toBeDisabled();
  });

  it("starts location tracking when clicked without position", () => {
    const store = createTestStore({
      geolocation: {
        ...geolocationInitialState,
        position: null,
        watchId: null,
      },
    });

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    const locationButton = screen.getByTestId("location-button");

    fireEvent.click(locationButton);

    expect(mockStartLocationTracking).toHaveBeenCalledTimes(2);
  });

  it("does not start tracking again if already watching", () => {
    const store = createTestStore({
      geolocation: {
        ...geolocationInitialState,
        position: null,
        watchId: "existing-watch-id",
      },
    });

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    const locationButton = screen.getByTestId("location-button");

    fireEvent.click(locationButton);

    expect(mockStartLocationTracking).toHaveBeenCalledTimes(1);
  });

  it("shows button as enabled when error occurs", () => {
    const store = createTestStore({
      geolocation: {
        ...geolocationInitialState,
        position: null,
        loading: false,
        error: "Location not available",
      },
    });

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    const locationButton = screen.getByTestId("location-button");

    expect(locationButton).not.toBeDisabled();
  });

  it("does not start tracking additional times when already watching", () => {
    const store = createTestStore({
      geolocation: {
        ...geolocationInitialState,
        position: null,
        watchId: "existing-watch-id",
      },
    });

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    const locationButton = screen.getByTestId("location-button");

    fireEvent.click(locationButton);
    fireEvent.click(locationButton);

    expect(mockStartLocationTracking).toHaveBeenCalledTimes(1);
  });
});
