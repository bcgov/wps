vi.mock("@/utils/storage", () => ({
  writeToFileSystem: vi.fn(),
  readFromFilesystem: vi.fn(),
  FIRE_CENTRES_KEY: "fireCentres",
  FIRE_CENTRES_CACHE_EXPIRATION: 12,
}));

vi.mock("api/psuAPI", () => ({
  getFireCentres: vi.fn(),
}));

import { createTestStore } from "@/testUtils";
import { FIRE_CENTRES_KEY, readFromFilesystem } from "@/utils/storage";
import { getFireCentres } from "api/psuAPI";
import type { FireCentre } from "@/types/fireCentre";
import { DateTime } from "luxon";
import { describe, expect, it, Mock, vi } from "vitest";
import reducer, {
  fetchFireCentres,
  getFireCentresFailed,
  getFireCentresStart,
  getFireCentresSuccess,
  initialState,
} from "./fireCentresSlice";

describe("fireCentersSlice reducers", () => {
  it("should handle getFireCentresStart", () => {
    const nextState = reducer(initialState, getFireCentresStart());
    expect(nextState.loading).toBe(true);
    expect(nextState.error).toBeNull();
    expect(nextState.fireCentres).toEqual([]);
  });

  it("should handle getFireCentresFailed", () => {
    const errorMsg = "Network error";
    const nextState = reducer(initialState, getFireCentresFailed(errorMsg));
    expect(nextState.loading).toBe(false);
    expect(nextState.error).toBe(errorMsg);
  });

  it("should handle getFireCentresSuccess", () => {
    const mockData: FireCentre[] = [{ id: 1, name: "Center A" }];
    const nextState = reducer(initialState, getFireCentresSuccess(mockData));
    expect(nextState.loading).toBe(false);
    expect(nextState.error).toBeNull();
    expect(nextState.fireCentres).toEqual(mockData);
  });
});

describe("fetchFireCentres thunk", () => {
  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();
  });
  const today = DateTime.now().toISO();
  const yesterday = DateTime.now().plus({ days: -1 }).toISO();
  const mockFireCentreA: FireCentre = {
    id: 1,
    name: "test",
  };
  const mockFireCentreB: FireCentre = {
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
      if (key === FIRE_CENTRES_KEY) {
        return {
          lastUpdated: isStale ? yesterday : today,
          data: isStale ? [mockFireCentreA] : [mockFireCentreB],
        };
      } else {
        return null;
      }
    });
  };

  it("should call API and dispatch success when cache is empty", async () => {
    mockCacheWithNoData();
    (getFireCentres as Mock).mockResolvedValue({
      fire_centres: [mockFireCentreA],
    });
    const store = createTestStore({
      fireCentres: { ...initialState },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
    });
    await store.dispatch(fetchFireCentres());
    const state = store.getState().fireCentres;
    expect(state.fireCentres).toEqual([mockFireCentreA]);
    expect(state.loading).toBe(false);
    expect(getFireCentres).toHaveBeenCalledOnce();
  });

  it("should call API and dispatch success when cache is stale", async () => {
    mockCacheWithData(true);
    (getFireCentres as Mock).mockResolvedValue({
      fire_centres: [mockFireCentreB],
    });
    const store = createTestStore({
      fireCentres: { ...initialState },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
    });
    await store.dispatch(fetchFireCentres());
    const state = store.getState().fireCentres;
    expect(state.fireCentres).toEqual([mockFireCentreB]);
    expect(state.loading).toBe(false);
    expect(getFireCentres).toHaveBeenCalledOnce();
  });

  it("should not call API when cache is fresh", async () => {
    mockCacheWithData(false);
    const store = createTestStore({
      fireCentres: { ...initialState },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
    });
    await store.dispatch(fetchFireCentres());
    const state = store.getState().fireCentres;
    expect(state.fireCentres).toEqual([mockFireCentreB]);
    expect(state.loading).toBe(false);
    expect(getFireCentres).not.toBeCalled();
  });

  it("should dispatch error when cache is empty and app is offline", async () => {
    mockCacheWithNoData();
    const store = createTestStore({
      fireCentres: { ...initialState },
      networkStatus: {
        networkStatus: { connected: false, connectionType: "none" },
      },
    });
    await store.dispatch(fetchFireCentres());
    const state = store.getState().fireCentres;
    expect(state.loading).toBe(false);
    expect(state.error).toMatch(/Unable to refresh fire centre data/);
  });

  it("should dispatch success when cache is stale and app is offline", async () => {
    mockCacheWithData(true);
    const store = createTestStore({
      fireCentres: { ...initialState },
      networkStatus: {
        networkStatus: { connected: false, connectionType: "none" },
      },
    });
    await store.dispatch(fetchFireCentres());
    const state = store.getState().fireCentres;
    expect(state.loading).toBe(false);
    expect(state.fireCentres).toEqual([mockFireCentreA]);
  });
});
