import { describe, it, expect, vi, Mock } from "vitest";
import reducer, {
  initialState,
  getRunParametersStart,
  getRunParametersFailed,
  getRunParametersSuccess,
  fetchSFMSRunParameters,
  selectRunParameters,
  } from "@/slices/runParametersSlice";
import { RunParameter, RunType } from "api/fbaAPI";
import { DateTime } from "luxon";
import {
  createTestStore
} from "@/testUtils";

// Mocks
vi.mock(import("api/fbaAPI"), async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    getMostRecentRunParameters: vi.fn(),
  }
})

vi.mock("@/utils/storage", () => ({
  writeToFileSystem: vi.fn(),
  readFromFilesystem: vi.fn(),
  RUN_PARAMETERS_CACHE_KEY: "runParameters",
}));

import { getMostRecentRunParameters } from "api/fbaAPI";
import { writeToFileSystem, readFromFilesystem } from "@/utils/storage";
import { RootState } from "@/store";

const today = DateTime.now().toISODate();
const tomorrow = DateTime.now().plus({ days: 1 }).toISODate();

const mockRunParameters: { [key: string]: RunParameter } = {
  [today]: {
    for_date: today,
    run_datetime: "2025-08-27T08:00:00Z",
    run_type: RunType.FORECAST,
  },
  [tomorrow]: {
    for_date: tomorrow,
    run_datetime: "2025-08-28T08:00:00Z",
    run_type: RunType.FORECAST,
  },
};

describe("runParameters reducer", () => {
  it("should handle getRunParametersStart", () => {
    const nextState = reducer(initialState, getRunParametersStart());
    expect(nextState.loading).toBe(true);
    expect(nextState.error).toBeNull();
  });

  it("should handle getRunParametersFailed", () => {
    const error = "Failed to fetch";
    const nextState = reducer(initialState, getRunParametersFailed(error));
    expect(nextState.loading).toBe(false);
    expect(nextState.error).toBe(error);
  });

  it("should handle getRunParametersSuccess", () => {
    const nextState = reducer(
      initialState,
      getRunParametersSuccess({ runParameters: mockRunParameters })
    );
    expect(nextState.loading).toBe(false);
    expect(nextState.error).toBeNull();
    expect(nextState.runParameters).toEqual(mockRunParameters);
  });
});

describe("fetchSFMSRunParameters thunk", () => {
  it("dispatches success when online and API returns data", async () => {
    (getMostRecentRunParameters as Mock).mockResolvedValue(mockRunParameters);
    (writeToFileSystem as Mock).mockResolvedValue(undefined);
    const store = createTestStore({
      runParameters: { ...initialState },
      networkStatus: { networkStatus: { connected: true, connectionType: "wifi" } },
    });
    await store.dispatch(fetchSFMSRunParameters())
    expect(store.getState().runParameters.runParameters).toBe(mockRunParameters)
  });

  it("dispatches failure when API throws", async () => {
    const errorMessage = "API error";
    (getMostRecentRunParameters as Mock).mockRejectedValue(new Error(errorMessage));
    const store = createTestStore({
      runParameters: { ...initialState },
      networkStatus: { networkStatus: { connected: true, connectionType: "wifi" } },
    });
    await store.dispatch(fetchSFMSRunParameters());
    expect(store.getState().runParameters.error).toContain(errorMessage)
  });

  it("dispatches success from cache when offline", async () => {
    (readFromFilesystem as Mock).mockResolvedValue({ data: mockRunParameters });
    const store = createTestStore({
      runParameters: { ...initialState },
      networkStatus: { networkStatus: { connected: false, connectionType: "none" } },
    });
    await store.dispatch(fetchSFMSRunParameters());
    expect(store.getState().runParameters.runParameters).toBe(mockRunParameters);
  });

  it("dispatches failure when offline and no cache", async () => {
    (readFromFilesystem as Mock).mockResolvedValue(null);
    const store = createTestStore({
      runParameters: { ...initialState },
      networkStatus: { networkStatus: { connected: false, connectionType: "none" } },
    });
    await store.dispatch(fetchSFMSRunParameters());
    expect(store.getState().runParameters.error).toBe("No run parameters available.")
  });
});

describe("selectRunParameters", () => {
  it("should return runParameters from state", () => {
    const state = {
      runParameters: {
        ...initialState,
        runParameters: mockRunParameters,
      },
    };
    const result = selectRunParameters(state as RootState);
    expect(result).toEqual(mockRunParameters);
  });
});
