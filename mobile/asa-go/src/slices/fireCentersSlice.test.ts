vi.mock("@/utils/storage", () => ({
  writeToFileSystem: vi.fn(),
  readFromFilesystem: vi.fn(),
  FIRE_CENTERS_KEY: "fireCenters",
  FIRE_CENTERS_CACHE_EXPIRATION: 12,
}));

vi.mock("api/fbaAPI", () => ({
  getFBAFireCenters: vi.fn(),
}));

import { createTestStore } from "@/testUtils";
import { FIRE_CENTERS_KEY, readFromFilesystem } from "@/utils/storage";
import { FireCenter, getFBAFireCenters } from "api/fbaAPI";
import { DateTime } from "luxon";
import { describe, expect, it, Mock, vi } from "vitest";
import reducer, {
  fetchFireCenters,
  getFireCentersFailed,
  getFireCentersStart,
  getFireCentersSuccess,
  initialState,
} from "./fireCentersSlice";

describe("fireCentersSlice reducers", () => {
  it("should handle getFireCentersStart", () => {
    const nextState = reducer(initialState, getFireCentersStart());
    expect(nextState.loading).toBe(true);
    expect(nextState.error).toBeNull();
    expect(nextState.fireCenters).toEqual([]);
  });

  it("should handle getFireCentersFailed", () => {
    const errorMsg = "Network error";
    const nextState = reducer(initialState, getFireCentersFailed(errorMsg));
    expect(nextState.loading).toBe(false);
    expect(nextState.error).toBe(errorMsg);
  });

  it("should handle getFireCentersSuccess", () => {
    const mockData: FireCenter[] = [
      { id: 1, name: "Center A", stations: [] } as FireCenter,
    ];
    const nextState = reducer(initialState, getFireCentersSuccess(mockData));
    expect(nextState.loading).toBe(false);
    expect(nextState.error).toBeNull();
    expect(nextState.fireCenters).toEqual(mockData);
  });
});

describe("fetchFireCenters thunk", () => {
  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();
  });
  const today = DateTime.now().toISO();
  const yesterday = DateTime.now().plus({ days: -1 }).toISO();
  const mockFireCenterA: FireCenter = {
    id: 1,
    name: "test",
    stations: [],
  };
  const mockFireCenterB: FireCenter = {
    id: 2,
    name: "foo",
    stations: [],
  };
  const mockCacheWithNoData = () => {
    (readFromFilesystem as Mock).mockImplementation(() => {
      console.log("Reading from null file system");
      return null;
    });
  };
  const mockCacheWithData = (isStale: boolean) => {
    (readFromFilesystem as Mock).mockImplementation((_filesystem, key) => {
      if (key === FIRE_CENTERS_KEY) {
        return {
          lastUpdated: isStale ? yesterday : today,
          data: isStale ? [mockFireCenterA] : [mockFireCenterB],
        };
      } else {
        return null;
      }
    });
  };

  it("should call API and dispatch success when cache is empty", async () => {
    mockCacheWithNoData();
    (getFBAFireCenters as Mock).mockResolvedValue({
      fire_centers: [mockFireCenterA],
    });
    const store = createTestStore({
      fireCenters: { ...initialState },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
    });
    await store.dispatch(fetchFireCenters());
    const state = store.getState().fireCenters;
    expect(state.fireCenters).toEqual([mockFireCenterA]);
    expect(state.loading).toBe(false);
    expect(getFBAFireCenters).toHaveBeenCalledOnce();
  });

  it("should call API and dispatch success when cache is stale", async () => {
    mockCacheWithData(true);
    (getFBAFireCenters as Mock).mockResolvedValue({
      fire_centers: [mockFireCenterB],
    });
    const store = createTestStore({
      fireCenters: { ...initialState },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
    });
    await store.dispatch(fetchFireCenters());
    const state = store.getState().fireCenters;
    expect(state.fireCenters).toEqual([mockFireCenterB]);
    expect(state.loading).toBe(false);
    expect(getFBAFireCenters).toHaveBeenCalledOnce();
  });

  it("should not call API when cache is fresh", async () => {
    mockCacheWithData(false);
    const store = createTestStore({
      fireCenters: { ...initialState },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
    });
    await store.dispatch(fetchFireCenters());
    const state = store.getState().fireCenters;
    expect(state.fireCenters).toEqual([mockFireCenterB]);
    expect(state.loading).toBe(false);
    expect(getFBAFireCenters).not.toBeCalled();
  });

  it("should dispatch error when cache is empty and app is offline", async () => {
    mockCacheWithNoData();
    const store = createTestStore({
      fireCenters: { ...initialState },
      networkStatus: {
        networkStatus: { connected: false, connectionType: "none" },
      },
    });
    await store.dispatch(fetchFireCenters());
    const state = store.getState().fireCenters;
    expect(state.loading).toBe(false);
    expect(state.error).toMatch(/Unable to refresh fire center data/);
  });

  it("should dispatch success when cache is stale and app is offline", async () => {
    mockCacheWithData(true);
    const store = createTestStore({
      fireCenters: { ...initialState },
      networkStatus: {
        networkStatus: { connected: false, connectionType: "none" },
      },
    });
    await store.dispatch(fetchFireCenters());
    const state = store.getState().fireCenters;
    expect(state.loading).toBe(false);
    expect(state.fireCenters).toEqual([mockFireCenterA])
  });

  it("should dispatch error when cache is empty and app is offline", async () => {
    mockCacheWithNoData();
    const store = createTestStore({
      fireCenters: { ...initialState },
      networkStatus: {
        networkStatus: { connected: false, connectionType: "none" },
      },
    });
    await store.dispatch(fetchFireCenters());
    const state = store.getState().fireCenters;
    expect(state.loading).toBe(false);
    expect(state.error).toMatch(/Unable to refresh fire center data/);
  });
});
