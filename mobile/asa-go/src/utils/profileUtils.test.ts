import { FireZoneTPIStats } from "@/api/fbaAPI";
import { hasRequiredFields } from "@/utils/profileUtils";

describe("hasRequiredFields", () => {
  it("should return true when all required fields are present", () => {
    const mockTPIStats: FireZoneTPIStats = {
      fire_zone_id: 1,
      valley_bottom_hfi: 10,
      valley_bottom_tpi: 20,
      mid_slope_hfi: 30,
      mid_slope_tpi: 40,
      upper_slope_hfi: 50,
      upper_slope_tpi: 60,
    };

    const result = hasRequiredFields(mockTPIStats);
    expect(result).toBe(true);
  });

  it("should return false when valley_bottom_hfi is undefined", () => {
    const mockTPIStats: FireZoneTPIStats = {
      fire_zone_id: 1,
      valley_bottom_hfi: undefined,
      valley_bottom_tpi: 20,
      mid_slope_hfi: 30,
      mid_slope_tpi: 40,
      upper_slope_hfi: 50,
      upper_slope_tpi: 60,
    };

    const result = hasRequiredFields(mockTPIStats);
    expect(result).toBe(false);
  });

  it("should return false when valley_bottom_tpi is null", () => {
    const mockTPIStats: FireZoneTPIStats = {
      fire_zone_id: 1,
      valley_bottom_hfi: 10,
      valley_bottom_tpi: null as unknown as number,
      mid_slope_hfi: 30,
      mid_slope_tpi: 40,
      upper_slope_hfi: 50,
      upper_slope_tpi: 60,
    };

    const result = hasRequiredFields(mockTPIStats);
    expect(result).toBe(false);
  });

  it("should return false when mid_slope_hfi is undefined", () => {
    const mockTPIStats: FireZoneTPIStats = {
      fire_zone_id: 1,
      valley_bottom_hfi: 10,
      valley_bottom_tpi: 20,
      mid_slope_hfi: undefined,
      mid_slope_tpi: 40,
      upper_slope_hfi: 50,
      upper_slope_tpi: 60,
    };

    const result = hasRequiredFields(mockTPIStats);
    expect(result).toBe(false);
  });

  it("should return false when mid_slope_tpi is undefined", () => {
    const mockTPIStats: FireZoneTPIStats = {
      fire_zone_id: 1,
      valley_bottom_hfi: 10,
      valley_bottom_tpi: 20,
      mid_slope_hfi: 30,
      mid_slope_tpi: undefined,
      upper_slope_hfi: 50,
      upper_slope_tpi: 60,
    };

    const result = hasRequiredFields(mockTPIStats);
    expect(result).toBe(false);
  });

  it("should return false when upper_slope_hfi is undefined", () => {
    const mockTPIStats: FireZoneTPIStats = {
      fire_zone_id: 1,
      valley_bottom_hfi: 10,
      valley_bottom_tpi: 20,
      mid_slope_hfi: 30,
      mid_slope_tpi: 40,
      upper_slope_hfi: undefined,
      upper_slope_tpi: 60,
    };

    const result = hasRequiredFields(mockTPIStats);
    expect(result).toBe(false);
  });

  it("should return false when upper_slope_tpi is undefined", () => {
    const mockTPIStats: FireZoneTPIStats = {
      fire_zone_id: 1,
      valley_bottom_hfi: 10,
      valley_bottom_tpi: 20,
      mid_slope_hfi: 30,
      mid_slope_tpi: 40,
      upper_slope_hfi: 50,
      upper_slope_tpi: undefined,
    };

    const result = hasRequiredFields(mockTPIStats);
    expect(result).toBe(false);
  });

  it("should return false when multiple fields are missing", () => {
    const mockTPIStats: FireZoneTPIStats = {
      fire_zone_id: 1,
      valley_bottom_hfi: undefined,
      valley_bottom_tpi: undefined,
      mid_slope_hfi: undefined,
      mid_slope_tpi: 40,
      upper_slope_hfi: 50,
      upper_slope_tpi: 60,
    };

    const result = hasRequiredFields(mockTPIStats);
    expect(result).toBe(false);
  });

  it("should return true when all fields are 0 (valid numbers)", () => {
    const mockTPIStats: FireZoneTPIStats = {
      fire_zone_id: 1,
      valley_bottom_hfi: 0,
      valley_bottom_tpi: 0,
      mid_slope_hfi: 0,
      mid_slope_tpi: 0,
      upper_slope_hfi: 0,
      upper_slope_tpi: 0,
    };

    const result = hasRequiredFields(mockTPIStats);
    expect(result).toBe(true);
  });

  it("should return true when all fields are negative numbers", () => {
    const mockTPIStats: FireZoneTPIStats = {
      fire_zone_id: 1,
      valley_bottom_hfi: -10,
      valley_bottom_tpi: -20,
      mid_slope_hfi: -30,
      mid_slope_tpi: -40,
      upper_slope_hfi: -50,
      upper_slope_tpi: -60,
    };

    const result = hasRequiredFields(mockTPIStats);
    expect(result).toBe(true);
  });
});
