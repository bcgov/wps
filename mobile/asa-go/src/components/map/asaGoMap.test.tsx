import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { DateTime } from "luxon";
import { describe, expect, it, vi, beforeEach } from "vitest";
import ASAGoMap, { ASAGoMapProps } from "@/components/map/ASAGoMap";
import {
  createTestStore,
  setupOpenLayersMocks,
  baseLayerMock,
} from "@/testUtils";
import { geolocationInitialState } from "@/slices/geolocationSlice";
import { RunType } from "@/api/fbaAPI";

setupOpenLayersMocks();
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

vi.mock("@/layerDefinitions", async () => {
  const actual = await import("@/layerDefinitions");

  return {
    ...actual,
    createHFILayer: vi
      .fn()
      .mockImplementation(() => Promise.resolve(baseLayerMock)),
  };
});

import { createHFILayer } from "@/layerDefinitions";

describe("ASAGoMap", () => {
  beforeAll(() => {
    window.ResizeObserver = ResizeObserver;
  });

  const defaultProps: ASAGoMapProps = {
    testId: "asa-go-map",
    selectedFireShape: undefined,
    setSelectedFireShape: vi.fn(),
    setSelectedFireCenter: vi.fn(),
    advisoryThreshold: 0,
    date: DateTime.fromISO("2024-12-15"),
    setDate: vi.fn(),
    setTab: vi.fn(),
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

  it("calls createHFILayer when date, runType, or runDatetime changes", async () => {
    const runParameter = {
      forDate: "2024-12-15",
      runDatetime: "2024-12-15T15:00:00Z",
      runType: RunType.FORECAST,
      loading: false,
      error: null,
    };
    const store = createTestStore({
      runParameter: runParameter,
    });

    const { rerender } = render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    // initial call
    expect(createHFILayer).toHaveBeenCalledTimes(1);
    expect(createHFILayer).toHaveBeenCalledWith(
      expect.objectContaining({
        filename: "hfi.pmtiles",
        for_date: DateTime.fromISO("2024-12-15"),
        run_type: RunType.FORECAST,
        run_date: DateTime.fromISO("2024-12-15T15:00:00Z"),
      })
    );

    store.dispatch({
      type: "runParameter/getRunParameterSuccess",
      payload: {
        forDate: "2024-12-16",
        runDateTime: "2024-12-16T23:00:00Z",
        runType: RunType.FORECAST,
      },
    });
    rerender(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} date={DateTime.fromISO("2024-12-16")} />
      </Provider>
    );
    expect(createHFILayer).toHaveBeenCalledWith(
      expect.objectContaining({
        filename: "hfi.pmtiles",
        for_date: DateTime.fromISO("2024-12-16"),
        run_type: RunType.FORECAST,
        run_date: DateTime.fromISO("2024-12-16T23:00:00Z"),
      })
    );
  });
});
