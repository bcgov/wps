import { render, screen, waitFor, within } from "@testing-library/react";
import { Provider } from "react-redux";
import { DateTime } from "luxon";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { userEvent } from "@testing-library/user-event";
import ASAGoMap, { ASAGoMapProps } from "@/components/map/ASAGoMap";
import {
  createTestStore,
  setupOpenLayersMocks,
  createLayerMock,
} from "@/testUtils";
import { geolocationInitialState } from "@/slices/geolocationSlice";
import { RunType } from "@/api/fbaAPI";
import * as mapView from "@/components/map/mapView";

vi.mock("@capacitor/filesystem", () => ({
  Filesystem: {
    readFile: vi.fn().mockResolvedValue({ data: JSON.stringify({}) }),
    writeFile: vi.fn().mockResolvedValue(undefined),
  },
  Directory: { Data: "DATA" },
  Encoding: { UTF8: "utf8" },
}));

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
      .mockImplementation(() => Promise.resolve(createLayerMock("HFILayer"))),
    createBasemapLayer: vi
      .fn()
      .mockImplementation(() =>
        Promise.resolve(createLayerMock("vectorBasemapLayer"))
      ),
  };
});

import { createHFILayer, HFI_LAYER_NAME } from "@/layerDefinitions";

describe("ASAGoMap", () => {
  beforeAll(() => {
    window.ResizeObserver = ResizeObserver;
  });

  const defaultProps: ASAGoMapProps = {
    testId: "asa-go-map",
    selectedFireShape: undefined,
    setSelectedFireShape: vi.fn(),
    setSelectedFireCenter: vi.fn(),
    advisoryThreshold: 20,
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
      }),
      true
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
      }),
      true
    );
  });
  it("renders the layer switcher button and legend on click", async () => {
    const store = createTestStore();

    const { getByTestId } = render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    const legendButton = getByTestId("legend-toggle-button");
    expect(legendButton).toBeInTheDocument();

    await userEvent.click(legendButton);
    const legendPopover = getByTestId("asa-go-map-legend-popover");
    expect(legendPopover).toBeInTheDocument();
  });

  it("calls handleLayerVisibilityChange and updates layerVisibility state", async () => {
    const store = createTestStore();
    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    // Open legend popover
    const legendButton = screen.getByTestId("legend-toggle-button");
    await userEvent.click(legendButton);

    // Find a layer toggle (simulate Zone Status layer toggle)
    const zoneStatusToggle = screen.getByTestId("zone-checkbox");
    const zoneStatusCheckbox = within(zoneStatusToggle).getByRole("checkbox");
    expect(zoneStatusToggle).toBeInTheDocument();

    // Toggle off
    await userEvent.click(zoneStatusToggle);

    // The toggle should now be unchecked
    expect(zoneStatusCheckbox).not.toBeChecked();

    // Toggle on
    await userEvent.click(zoneStatusToggle);
    expect(zoneStatusCheckbox).toBeChecked();
  });

  it("calls setZoneStatusLayerVisibility for ZONE_STATUS_LAYER_NAME", async () => {
    const store = createTestStore();
    const setZoneStatusLayerVisibilityMock = vi.spyOn(
      await import("@/components/map/layerVisibility"),
      "setZoneStatusLayerVisibility"
    );

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    // Open legend popover
    const legendButton = screen.getByTestId("legend-toggle-button");
    await userEvent.click(legendButton);

    // Toggle Zone Status layer
    const zoneStatusToggle = screen.getByTestId("zone-checkbox");
    const zoneStatusCheckbox = within(zoneStatusToggle).getByRole("checkbox");
    await waitFor(() => expect(zoneStatusCheckbox).toBeChecked());
    await userEvent.click(zoneStatusToggle);

    expect(setZoneStatusLayerVisibilityMock).toHaveBeenCalled();
    expect(setZoneStatusLayerVisibilityMock).toHaveBeenCalledWith(
      expect.any(Object), // layer instance
      expect.any(Array), // fireShapeAreas
      20, // advisoryThreshold
      false // visibility
    );
    await waitFor(() => expect(zoneStatusCheckbox).not.toBeChecked());

    await userEvent.click(zoneStatusToggle);
    expect(setZoneStatusLayerVisibilityMock).toHaveBeenCalledWith(
      expect.any(Object), // layer instance
      expect.any(Array), // fireShapeAreas
      20, // advisoryThreshold
      true // visibility
    );
    await waitFor(() => expect(zoneStatusCheckbox).toBeChecked());
  });
  it("calls setDefaultLayerVisibility on the correct layer", async () => {
    const store = createTestStore();
    const setDefaultLayerVisibilityMock = vi.spyOn(
      await import("@/components/map/layerVisibility"),
      "setDefaultLayerVisibility"
    );
    const mockToggleLayersRef = {
      hfiVectorLayer: null,
    };

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    // Open legend popover
    const legendButton = screen.getByTestId("legend-toggle-button");
    await userEvent.click(legendButton);

    // Toggle HFI layer
    const hfiToggle = screen.getByTestId("hfi-checkbox");
    // should be checked at first
    const hfiCheckbox = within(hfiToggle).getByRole("checkbox");
    await waitFor(() => expect(hfiCheckbox).toBeChecked());
    await userEvent.click(hfiToggle);

    // test that we're turning it off
    expect(setDefaultLayerVisibilityMock).toHaveBeenCalledWith(
      mockToggleLayersRef,
      HFI_LAYER_NAME,
      false
    );
    await waitFor(() => expect(hfiCheckbox).not.toBeChecked());
  });

  it("calls save and load map view state", async () => {
    const store = createTestStore({
      geolocation: {
        ...geolocationInitialState,
        position: mockPosition,
      },
    });
    const loadMapViewStateMock = vi.spyOn(mapView, "loadMapViewState");

    render(
      <Provider store={store}>
        <ASAGoMap {...defaultProps} />
      </Provider>
    );

    expect(loadMapViewStateMock).toHaveBeenCalled();
  });
});
