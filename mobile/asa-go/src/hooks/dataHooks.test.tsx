import { describe, it, expect, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { DateTime } from "luxon";
import {
  useFilteredHFIStatsForDate,
  useFireShapeAreasForDate,
  useProvincialSummaryForDate,
  useTPIStatsForDate,
} from "@/hooks/dataHooks";
import {
  FireShapeArea,
  FireShapeAreaDetail,
  FireZoneHFIStatsDictionary,
  FireZoneTPIStats,
  RunParameter,
  RunType,
} from "@/api/fbaAPI";
import { filterHFIFuelStatsByArea } from "@/utils/hfiStatsUtils";
import { RootState } from "@/store";
import { initialState } from "@/slices/dataSlice";
import { ReactNode } from "react";

vi.mock("@/utils/hfiStatsUtils", () => ({
  filterHFIFuelStatsByArea: vi.fn((data) => data), // mock passthrough
}));

const today = DateTime.now();
const todayKey = today.toISODate();

const mockRunParameter: RunParameter = {
  run_type: RunType.FORECAST,
  run_datetime: "2025-11-20T00:00:00Z",
  for_date: todayKey,
};

const createMockStore = (state: Partial<RootState>) =>
  configureStore({
    reducer: () => state,
  });

describe("Custom Hooks", () => {
  it("useFilteredHFIStatsForDate returns filtered HFI stats", () => {
    const mockHFIStats: FireZoneHFIStatsDictionary = {
      2: {
        min_wind_stats: [],
        fuel_area_stats: [],
      },
    };
    const store = createMockStore({
      data: {
        ...initialState,
        hfiStats: {
          [todayKey]: { runParameter: mockRunParameter, data: mockHFIStats },
        },
      },
    });

    const { result } = renderHook(() => useFilteredHFIStatsForDate(today), {
      wrapper: ({ children }: { children: ReactNode }) => (
        <Provider store={store}>{children}</Provider>
      ),
    });

    expect(result.current).toEqual(mockHFIStats);
    expect(filterHFIFuelStatsByArea).toHaveBeenCalledWith(mockHFIStats);
  });

  it("useFilteredHFIStatsForDate returns [] when data is missing", () => {
    const store = createMockStore({ data: { ...initialState, hfiStats: {} } });

    const { result } = renderHook(() => useFilteredHFIStatsForDate(today), {
      wrapper: ({ children }: { children: ReactNode }) => (
        <Provider store={store}>{children}</Provider>
      ),
    });

    expect(result.current).toEqual([]);
  });

  it("useFireShapeAreasForDate returns FireShapeAreas", () => {
    const mockAreas: FireShapeArea[] = [{ fire_shape_id: 1 } as FireShapeArea];
    const store = createMockStore({
      data: {
        ...initialState,
        fireShapeAreas: {
          [todayKey]: { runParameter: mockRunParameter, data: mockAreas },
        },
      },
    });

    const { result } = renderHook(() => useFireShapeAreasForDate(today), {
      wrapper: ({ children }: { children: ReactNode }) => (
        <Provider store={store}>{children}</Provider>
      ),
    });

    expect(result.current).toEqual(mockAreas);
  });

  it("useProvincialSummaryForDate groups by fire_centre_name", () => {
    const mockSummary: FireShapeAreaDetail[] = [
      { fire_shape_id: 1, fire_centre_name: "Centre A" } as FireShapeAreaDetail,
      { fire_shape_id: 2, fire_centre_name: "Centre A" } as FireShapeAreaDetail,
    ];
    const store = createMockStore({
      data: {
        ...initialState,
        provincialSummaries: {
          [todayKey]: { runParameter: mockRunParameter, data: mockSummary },
        },
      },
    });

    const { result } = renderHook(() => useProvincialSummaryForDate(today), {
      wrapper: ({ children }: { children: ReactNode }) => (
        <Provider store={store}>{children}</Provider>
      ),
    });

    expect(result.current).toHaveProperty("Centre A");
    expect(result.current?.["Centre A"].length).toBe(2);
  });

  it("useTPIStatsForDate returns TPI stats", () => {
    const mockTPIStats: FireZoneTPIStats[] = [
      { fire_zone_id: 1 } as FireZoneTPIStats,
    ];
    const store = createMockStore({
      data: {
        ...initialState,
        tpiStats: {
          [todayKey]: { runParameter: mockRunParameter, data: mockTPIStats },
        },
      },
    });

    const { result } = renderHook(() => useTPIStatsForDate(today), {
      wrapper: ({ children }: { children: ReactNode }) => (
        <Provider store={store}>{children}</Provider>
      ),
    });

    expect(result.current).toEqual(mockTPIStats);
  });

  it("returns empty array or undefined when forDate is nil", () => {
    const store = createMockStore({
      data: {
        ...initialState,
        hfiStats: {},
        fireShapeAreas: {},
        provincialSummaries: {},
        tpiStats: {},
      },
    });

    const { result: hfiResult } = renderHook(
      () => useFilteredHFIStatsForDate(null as unknown as DateTime),
      {
        wrapper: ({ children }: { children: ReactNode }) => (
          <Provider store={store}>{children}</Provider>
        ),
      }
    );
    expect(hfiResult.current).toEqual([]);

    const { result: fireShapeResult } = renderHook(
      () => useFireShapeAreasForDate(null as unknown as DateTime),
      {
        wrapper: ({ children }: { children: ReactNode }) => (
          <Provider store={store}>{children}</Provider>
        ),
      }
    );
    expect(fireShapeResult.current).toEqual([]);

    const { result: provincialResult } = renderHook(
      () => useProvincialSummaryForDate(null as unknown as DateTime),
      {
        wrapper: ({ children }: { children: ReactNode }) => (
          <Provider store={store}>{children}</Provider>
        ),
      }
    );
    expect(provincialResult.current).toBeUndefined();

    const { result: tpiResult } = renderHook(
      () => useTPIStatsForDate(null as unknown as DateTime),
      {
        wrapper: ({ children }: { children: ReactNode }) => (
          <Provider store={store}>{children}</Provider>
        ),
      }
    );
    expect(tpiResult.current).toEqual([]);
  });
});
