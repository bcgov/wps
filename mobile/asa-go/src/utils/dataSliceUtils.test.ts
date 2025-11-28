import {
  FireShapeArea,
  getFireShapeAreas,
  getHFIStats,
  getProvincialSummary,
  getTPIStats,
  RunParameter,
  RunType,
} from "@/api/fbaAPI";
import {
  dataAreEqual,
  fetchFireShapeArea,
  fetchFireShapeAreas,
  fetchHFIStatsForRunParameter,
  fetchProvincialSummaries,
  fetchProvincialSummary,
  fetchTpiStatsForRunParameter,
  runParametersMatch,
  shapeDataForCaching,
} from "@/utils/dataSliceUtils";
import { CacheableData } from "@/utils/storage";
import { DateTime } from "luxon";
import { beforeEach, describe, expect, it, Mock, vi } from "vitest";

vi.mock("@/api/fbaAPI", async () => {
  const actual = await vi.importActual<typeof import("@/api/fbaAPI")>(
    "@/api/fbaAPI"
  );
  return {
    ...actual,
    getFireShapeAreas: vi.fn(),
    getHFIStats: vi.fn(),
    getTPIStats: vi.fn(),
    getProvincialSummary: vi.fn(),
  };
});

const mockRunParameter: RunParameter = {
  run_type: RunType.FORECAST,
  run_datetime: "2025-11-20T00:00:00Z",
  for_date: "2025-11-21",
};

const today = DateTime.now();
const todayKey = today.toISODate();
const tomorrowKey = today.plus({ days: 1 }).toISODate();

describe("Utility Functions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  describe("runParametersMatch", () => {
    it("returns true when runParameters match cached data", () => {
      const runParameters = {
        [todayKey]: mockRunParameter,
        [tomorrowKey]: mockRunParameter,
      };
      const data: CacheableData<FireShapeArea[]> = {
        [todayKey]: { runParameter: mockRunParameter, data: [] },
        [tomorrowKey]: { runParameter: mockRunParameter, data: [] },
      };

      expect(
        runParametersMatch(todayKey, tomorrowKey, runParameters, data)
      ).toBe(true);
    });

    it("returns false when runParameters differ", () => {
      const runParameters = {
        [todayKey]: mockRunParameter,
        [tomorrowKey]: { ...mockRunParameter, for_date: "2025-11-22" },
      };
      const data: CacheableData<FireShapeArea[]> = {
        [todayKey]: { runParameter: mockRunParameter, data: [] },
        [tomorrowKey]: { runParameter: mockRunParameter, data: [] },
      };

      expect(
        runParametersMatch(todayKey, tomorrowKey, runParameters, data)
      ).toBe(false);
    });
  });

  describe("shapeDataForCaching", () => {
    it("shapes data correctly", () => {
      const result = shapeDataForCaching(
        todayKey,
        tomorrowKey,
        { [todayKey]: mockRunParameter, [tomorrowKey]: mockRunParameter },
        [{ fire_shape_id: 1 } as FireShapeArea],
        [{ fire_shape_id: 2 } as FireShapeArea]
      );

      expect((result[todayKey].data[0] as FireShapeArea).fire_shape_id).toBe(1);
      expect((result[tomorrowKey].data[0] as FireShapeArea).fire_shape_id).toBe(
        2
      );
    });
  });

  describe("dataAreEqual", () => {
    it("returns true for equal data", () => {
      const a: CacheableData<FireShapeArea[]> = {
        [todayKey]: { runParameter: mockRunParameter, data: [] },
        [tomorrowKey]: { runParameter: mockRunParameter, data: [] },
      };
      const b = { ...a };

      expect(dataAreEqual(a, b)).toBe(true);
    });

    it("returns false for different data", () => {
      const a: CacheableData<FireShapeArea[]> = {
        [todayKey]: { runParameter: mockRunParameter, data: [] },
        [tomorrowKey]: { runParameter: mockRunParameter, data: [] },
      };
      const b: CacheableData<FireShapeArea[]> = {
        [todayKey]: {
          runParameter: mockRunParameter,
          data: [{ fire_shape_id: 1 } as FireShapeArea],
        },
        [tomorrowKey]: { runParameter: mockRunParameter, data: [] },
      };

      expect(dataAreEqual(a, b)).toBe(false);
    });
  });
});

describe("Async Fetch Functions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetchFireShapeArea returns empty array if runParameter is nil", async () => {
    const result = await fetchFireShapeArea(null as unknown as RunParameter);
    expect(result).toEqual([]);
  });

  it("fetchFireShapeArea calls API and returns shapes", async () => {
    (getFireShapeAreas as Mock).mockResolvedValue({
      shapes: [{ fire_shape_id: 1 }],
    });
    const result = await fetchFireShapeArea(mockRunParameter);
    expect(result).toEqual([{ fire_shape_id: 1 }]);
    expect(getFireShapeAreas).toHaveBeenCalledWith(
      mockRunParameter.run_type,
      mockRunParameter.run_datetime,
      mockRunParameter.for_date
    );
  });

  it("fetchFireShapeAreas returns shaped data", async () => {
    (getFireShapeAreas as Mock).mockResolvedValue({
      shapes: [{ fire_shape_id: 1 }],
    });
    const result = await fetchFireShapeAreas(todayKey, tomorrowKey, {
      [todayKey]: mockRunParameter,
      [tomorrowKey]: mockRunParameter,
    });
    expect(result[todayKey].data[0].fire_shape_id).toBe(1);
  });

  it("fetchHFIStatsForRunParameter returns zone_data", async () => {
    (getHFIStats as Mock).mockResolvedValue({ zone_data: { zone1: {} } });
    const result = await fetchHFIStatsForRunParameter(mockRunParameter);
    expect(result).toEqual({ zone1: {} });
  });

  it("fetchTpiStatsForRunParameter returns firezone_tpi_stats", async () => {
    (getTPIStats as Mock).mockResolvedValue({
      firezone_tpi_stats: [{ fire_zone_id: 1 }],
    });
    const result = await fetchTpiStatsForRunParameter(mockRunParameter);
    expect(result).toEqual([{ fire_zone_id: 1 }]);
  });

  it("fetchProvincialSummary returns provincial_summary", async () => {
    (getProvincialSummary as Mock).mockResolvedValue({
      provincial_summary: [{ fire_shape_id: 1 }],
    });
    const result = await fetchProvincialSummary(mockRunParameter);
    expect(result).toEqual([{ fire_shape_id: 1 }]);
  });

  it("fetchProvincialSummaries returns shaped data", async () => {
    (getProvincialSummary as Mock).mockResolvedValue({
      provincial_summary: [{ fire_shape_id: 1 }],
    });
    const result = await fetchProvincialSummaries(todayKey, "tomorrow", {
      [todayKey]: mockRunParameter,
      [tomorrowKey]: mockRunParameter,
    });
    expect(result[todayKey].data[0].fire_shape_id).toBe(1);
  });
});
