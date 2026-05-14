vi.mock("api/fbaAPI", async () => {
  const actual = await vi.importActual<typeof import("api/fbaAPI")>(
    "api/fbaAPI",
  );
  return {
    ...actual,
    getMostRecentRunParameters: vi.fn(),
  };
});

vi.mock("@/utils/storage", () => ({
  writeToFileSystem: vi.fn(),
  readFromFilesystem: vi.fn(),
  FIRE_CENTRES_KEY: "fireCentres",
  HFI_STATS_KEY: "hfiStats",
  PROVINCIAL_SUMMARY_KEY: "provincialSummary",
  RUN_PARAMETERS_CACHE_KEY: "runParameters",
  TPI_STATS_KEY: "tpiStats",
}));

vi.mock("@/utils/dataSliceUtils", async () => {
  const actual = await vi.importActual<typeof import("@/utils/dataSliceUtils")>(
    "@/utils/dataSliceUtils",
  );
  return {
    ...actual,
    fetchHFIStats: vi.fn(),
    fetchProvincialSummaries: vi.fn(),
    fetchTpiStats: vi.fn(),
  };
});

import reducer, {
  DataState,
  fetchAndCacheData,
  getDataFailed,
  getDataStart,
  getDataSuccess,
  initialState,
  setLastUpdated,
} from "@/slices/dataSlice";
import {
  fetchHFIStats,
  fetchProvincialSummaries,
  fetchTpiStats,
  getTodayKey,
  getTomorrowKey,
} from "@/utils/dataSliceUtils";
import { initialState as runParametersInitialState } from "@/slices/runParametersSlice";
import { createTestStore } from "@/testUtils";
import {
  CacheableData,
  HFI_STATS_KEY,
  PROVINCIAL_SUMMARY_KEY,
  readFromFilesystem,
  TPI_STATS_KEY,
} from "@/utils/storage";
import {
  AdvisoryCriticalHours,
  AdvisoryMinWindStats,
  FireShapeStatusDetail,
  FireZoneFuelStats,
  FireZoneHFIStatsDictionary,
  FireZoneStatus,
  FireZoneTPIStats,
  FuelType,
  HfiThreshold,
  RunParameter,
  RunType,
} from "api/fbaAPI";
import { DateTime } from "luxon";
import { describe, expect, it, Mock, vi } from "vitest";
import { AdvisoryStatus } from "@/utils/constants";

const todayKey = getTodayKey();
const tomorrowKey = getTomorrowKey();
const yesterdayKey = DateTime.fromISO(todayKey).minus({ days: 1 }).toISODate()!;
const lastUpdatedDate = "2026-04-22T16:30-07:00";

const mockYesterdayRunParameter = {
  for_date: yesterdayKey,
  run_datetime: "2025-08-27T08:00:00Z",
  run_type: RunType.FORECAST,
};

const mockTodayRunParameter = {
  for_date: todayKey,
  run_datetime: "2025-08-27T08:00:00Z",
  run_type: RunType.FORECAST,
};

const mockTomorrowRunParameter = {
  for_date: tomorrowKey,
  run_datetime: "2025-08-28T08:00:00Z",
  run_type: RunType.FORECAST,
};

const mockStaleRunParameters: { [key: string]: RunParameter } = {
  [yesterdayKey]: mockYesterdayRunParameter,
  [todayKey]: mockTodayRunParameter,
};

const mockRunParameters: { [key: string]: RunParameter } = {
  [todayKey]: mockTodayRunParameter,
  [tomorrowKey]: mockTomorrowRunParameter,
};

const mockFireShapeStatus: FireZoneStatus = {
  fire_shape_id: 1,
  status: AdvisoryStatus.ADVISORY,
};

const mockFireShapeStatusDetail: FireShapeStatusDetail = {
  ...mockFireShapeStatus,
  fire_shape_name: "test_fire_zone_unit",
  fire_centre_name: "test_fire_centre",
};

const mockStaleCacheableProvincialSummaries: CacheableData<
  FireShapeStatusDetail[]
> = {
  [yesterdayKey]: {
    runParameter: mockYesterdayRunParameter,
    data: [mockFireShapeStatusDetail],
  },
  [todayKey]: {
    runParameter: mockTodayRunParameter,
    data: [mockFireShapeStatusDetail],
  },
};

const mockCacheableProvincialSummaries: CacheableData<FireShapeStatusDetail[]> =
  {
    [todayKey]: {
      runParameter: mockTodayRunParameter,
      data: [mockFireShapeStatusDetail],
    },
    [tomorrowKey]: {
      runParameter: mockTomorrowRunParameter,
      data: [mockFireShapeStatusDetail],
    },
  };

const mockFireZoneTPIStats: FireZoneTPIStats = {
  fire_zone_id: 1,
  valley_bottom_hfi: 5,
  valley_bottom_tpi: 5,
  mid_slope_hfi: 10,
  mid_slope_tpi: 10,
  upper_slope_hfi: 15,
  upper_slope_tpi: 15,
};

const mockStaleCacheableFireZoneTPIStats: CacheableData<FireZoneTPIStats[]> = {
  [yesterdayKey]: {
    runParameter: mockYesterdayRunParameter,
    data: [mockFireZoneTPIStats],
  },
  [todayKey]: {
    runParameter: mockTodayRunParameter,
    data: [mockFireZoneTPIStats],
  },
};

const mockCacheableFireZoneTPIStats: CacheableData<FireZoneTPIStats[]> = {
  [todayKey]: {
    runParameter: mockTodayRunParameter,
    data: [mockFireZoneTPIStats],
  },
  [tomorrowKey]: {
    runParameter: mockTomorrowRunParameter,
    data: [mockFireZoneTPIStats],
  },
};

const mockHFIThreshold: HfiThreshold = {
  id: 1,
  name: "test",
  description: "test description",
};

const mockAdvisoryMinWindStats: AdvisoryMinWindStats = {
  threshold: mockHFIThreshold,
  min_wind_speed: 5,
};

const mockFuelType: FuelType = {
  fuel_type_id: 1,
  fuel_type_code: "C-3",
  description: "tree",
};

const mockAdvisoryCriticalHours: AdvisoryCriticalHours = {
  start_time: 10,
  end_time: 20,
};

const mockFireZoneFuelStats: FireZoneFuelStats = {
  fuel_type: mockFuelType,
  threshold: mockHFIThreshold,
  critical_hours: mockAdvisoryCriticalHours,
  area: 5,
  fuel_area: 10,
};

const mockFireZoneHFIStats: FireZoneHFIStats = {
  min_wind_stats: [mockAdvisoryMinWindStats],
  fuel_area_stats: [mockFireZoneFuelStats],
};

export interface FireZoneHFIStats {
  min_wind_stats: AdvisoryMinWindStats[];
  fuel_area_stats: FireZoneFuelStats[];
}

const mockStaleCacheableHFIStats: CacheableData<FireZoneHFIStatsDictionary> = {
  [yesterdayKey]: {
    runParameter: mockYesterdayRunParameter,
    data: {
      1: mockFireZoneHFIStats,
    },
  },
  [todayKey]: {
    runParameter: mockTodayRunParameter,
    data: {
      1: mockFireZoneHFIStats,
    },
  },
};

const mockCacheableHFIStats: CacheableData<FireZoneHFIStatsDictionary> = {
  [todayKey]: {
    runParameter: mockTodayRunParameter,
    data: {
      1: mockFireZoneHFIStats,
    },
  },
  [tomorrowKey]: {
    runParameter: mockTomorrowRunParameter,
    data: {
      1: mockFireZoneHFIStats,
    },
  },
};

const mockStaleData = {
  lastUpdated: yesterdayKey,
  provincialSummaries: mockStaleCacheableProvincialSummaries,
  tpiStats: mockStaleCacheableFireZoneTPIStats,
  hfiStats: mockStaleCacheableHFIStats,
};

const mockData = {
  lastUpdated: todayKey,
  provincialSummaries: mockCacheableProvincialSummaries,
  tpiStats: mockCacheableFireZoneTPIStats,
  hfiStats: mockCacheableHFIStats,
};

export const staleInitialState: DataState = {
  loading: false,
  error: null,
  ...mockStaleData,
};

describe("data reducer", () => {
  it("should handle getDataStart", () => {
    const nextState = reducer(initialState, getDataStart());
    expect(nextState.loading).toBe(true);
    expect(nextState.error).toBeNull();
  });

  it("should handle getDataFailed", () => {
    const error = "API error";
    const nextState = reducer(initialState, getDataFailed(error));
    expect(nextState.loading).toBe(false);
    expect(nextState.error).toBe(error);
  });

  it("should handle setLastUpdated", () => {
    const lastUpdated = "2025-09-02T10:00:00Z";
    const nextState = reducer(initialState, setLastUpdated({ lastUpdated }));
    expect(nextState.lastUpdated).toBe(lastUpdated);
  });

  it("should handle getDataSuccess", () => {
    const nextState = reducer(initialState, getDataSuccess({ ...mockData }));
    expect(nextState.loading).toBe(false);
    expect(nextState.error).toBeNull();
    expect(nextState.lastUpdated).toEqual(todayKey);
    expect(nextState.provincialSummaries).toEqual(
      mockCacheableProvincialSummaries,
    );
    expect(nextState.tpiStats).toEqual(mockCacheableFireZoneTPIStats);
    expect(nextState.hfiStats).toEqual(mockCacheableHFIStats);
  });
});

describe("fetchAndCacheData thunk", () => {
  const mockCacheWithData = () => {
    (readFromFilesystem as Mock).mockImplementation((_filesystem, key) => {
      switch (key) {
        case PROVINCIAL_SUMMARY_KEY:
          return {
            lastUpdated: lastUpdatedDate,
            data: mockCacheableProvincialSummaries,
          };
        case TPI_STATS_KEY:
          return {
            lastUpdated: lastUpdatedDate,
            data: mockCacheableFireZoneTPIStats,
          };
        case HFI_STATS_KEY:
          return {
            lastUpdated: lastUpdatedDate,
            data: mockCacheableHFIStats,
          };
      }
    });
  };
  const mockCacheWithNoData = () => {
    (readFromFilesystem as Mock).mockImplementation(() => {
      return null;
    });
  };
  const mockAPIData = () => {
    vi.mocked(fetchHFIStats).mockResolvedValue(mockCacheableHFIStats);
    vi.mocked(fetchProvincialSummaries).mockResolvedValue(
      mockCacheableProvincialSummaries,
    );
    vi.mocked(fetchTpiStats).mockResolvedValue(mockCacheableFireZoneTPIStats);
  };
  const testExpectedDataState = (dataState: DataState) => {
    expect(dataState.error).toBeNull();
    expect(dataState.provincialSummaries).toEqual(
      mockCacheableProvincialSummaries,
    );
    expect(dataState.tpiStats).toEqual(mockCacheableFireZoneTPIStats);
    expect(dataState.hfiStats).toEqual(mockCacheableHFIStats);
  };
  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();
  });
  it("should dispatch getDataFailed when runParameters is null", async () => {
    const store = createTestStore({
      data: { ...initialState },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
      runParameters: runParametersInitialState,
    });
    await store.dispatch(fetchAndCacheData());
    expect(store.getState().data.error).toMatch(/runParameters can't be null/);
  });

  it("should update state from cache when cache is current and state is empty", async () => {
    mockCacheWithData();
    const store = createTestStore({
      data: { ...initialState },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
      runParameters: {
        ...runParametersInitialState,
        runParameters: mockRunParameters,
      },
    });
    await store.dispatch(fetchAndCacheData());

    // API should not be called
    expect(fetchHFIStats).not.toHaveBeenCalled();
    expect(fetchProvincialSummaries).not.toHaveBeenCalled();
    expect(fetchTpiStats).not.toHaveBeenCalled();

    // redux store should be updated with the cached data
    const dataState = store.getState().data;
    testExpectedDataState(dataState);
    expect(dataState.lastUpdated).toBe(lastUpdatedDate);
  });
  it("should update state from cache when cache is current and state is stale", async () => {
    mockCacheWithData();
    const store = createTestStore({
      data: { ...staleInitialState },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
      runParameters: {
        ...runParametersInitialState,
        runParameters: mockRunParameters,
      },
    });
    await store.dispatch(fetchAndCacheData());

    // Utility functions which call the API should not be called
    expect(fetchHFIStats).not.toHaveBeenCalled();
    expect(fetchProvincialSummaries).not.toHaveBeenCalled();
    expect(fetchTpiStats).not.toHaveBeenCalled();

    // redux store should be updated with the cached data
    const dataState = store.getState().data;
    testExpectedDataState(dataState);
  });
  it("should update state from API calls when cache is empty and app is online", async () => {
    mockAPIData();
    mockCacheWithNoData();
    const store = createTestStore({
      data: { ...initialState },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
      runParameters: {
        ...runParametersInitialState,
        runParameters: mockRunParameters,
      },
    });
    await store.dispatch(fetchAndCacheData());

    // Utility functions which call the API should be called
    expect(fetchHFIStats).toHaveBeenCalled();
    expect(fetchProvincialSummaries).toHaveBeenCalled();
    expect(fetchTpiStats).toHaveBeenCalled();

    // redux store should be updated with the fetched data
    const dataState = store.getState().data;
    testExpectedDataState(dataState);
  });
  it("should update state from API calls when run parameters state is stale", async () => {
    mockAPIData();
    mockCacheWithData();
    const store = createTestStore({
      data: { ...initialState },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
      runParameters: {
        ...runParametersInitialState,
        runParameters: mockStaleRunParameters,
      },
    });
    await store.dispatch(fetchAndCacheData());

    // Utility functions which call the API should be called
    expect(fetchHFIStats).toHaveBeenCalled();
    expect(fetchProvincialSummaries).toHaveBeenCalled();
    expect(fetchTpiStats).toHaveBeenCalled();

    // redux store should be updated with the fetched data
    const dataState = store.getState().data;
    testExpectedDataState(dataState);
  });

  it("should dispatch getDataFailed when state is stale and app is offline", async () => {
    mockCacheWithData();
    const store = createTestStore({
      data: { ...initialState },
      networkStatus: {
        networkStatus: { connected: false, connectionType: "none" },
      },
      runParameters: {
        ...runParametersInitialState,
        runParameters: mockStaleRunParameters,
      },
    });
    await store.dispatch(fetchAndCacheData());
    expect(store.getState().data.error).toMatch(/Unable to update data/);
  });
});
