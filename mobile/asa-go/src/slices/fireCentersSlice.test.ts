vi.mock("@/utils/storage", () => ({
  writeToFileSystem: vi.fn(),
  readFromFilesystem: vi.fn(),
  FIRE_CENTERS_KEY: "fireCenters",
  FIRE_CENTERS_CACHE_EXPIRATION: 12,
}));

vi.mock("api/psuAPI", () => ({
  getFireCentres: vi.fn(),
}));

import { createTestStore } from "@/testUtils";
import { FIRE_CENTERS_KEY, readFromFilesystem } from "@/utils/storage";
import { getFireCentres } from "api/psuAPI";
import type { FireCentre } from "@/types/fireCentre";
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
    const mockData: FireCentre[] = [
      { id: 1, name: "Center A" } as FireCentre,
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
  const mockFireCenterA: FireCentre = {
    id: 1,
    name: "test",
  };
  const mockFireCenterB: FireCentre = {
    id: 2,
    name: "foo",
  };
  const mockCacheWithNoData = () => {
    (readFromFilesystem as Mock).mockImplementation(() => {
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
    (getFireCentres as Mock).mockResolvedValue({
      fire_centres: [mockFireCenterA],
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
    expect(getFireCentres).toHaveBeenCalledOnce();
  });

  it("should call API and dispatch success when cache is stale", async () => {
    mockCacheWithData(true);
    (getFireCentres as Mock).mockResolvedValue({
      fire_centres: [mockFireCenterB],
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
    expect(getFireCentres).toHaveBeenCalledOnce();
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
    expect(getFireCentres).not.toBeCalled();
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
    expect(state.fireCenters).toEqual([mockFireCenterA]);
  });
});
