import { AdvisoryMinWindStats, FireShapeAreaDetail } from "@/api/fbaAPI";
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from "@/featureStylers";
import {
  calculateStatusColour,
  calculateStatusText,
  calculateWindSpeedText,
  getWindSpeedMinimum,
} from "@/utils/calculateZoneStatus";
import { AdvisoryStatus } from "@/utils/constants";

const DEFAULT_COLOR = "#fff000";

const fireShapeDetails: FireShapeAreaDetail[] = [
  {
    fire_shape_id: 18,
    threshold: 1,
    combustible_area: 11014999365,
    elevated_hfi_area: 4158676298,
    elevated_hfi_percentage: 37,
    fire_shape_name: "C4-100 Mile House Fire Zone",
    fire_centre_name: "Cariboo Fire Centre",
  },
  {
    fire_shape_id: 18,
    threshold: 2,
    combustible_area: 11014999365,
    elevated_hfi_area: 2079887078,
    elevated_hfi_percentage: 18,
    fire_shape_name: "C4-100 Mile House Fire Zone",
    fire_centre_name: "Cariboo Fire Centre",
  },
];

const advisoryThreshold = {
  id: 1,
  name: "Advisory",
  description: "Advisory threshold",
};

const warningThreshold = {
  id: 2,
  name: "Warning",
  description: "Warning threshold",
};

describe("calculateStatusColour", () => {
  it("returns the default color when FireShapeArea array is empty", () => {
    const result = calculateStatusColour([], 20, DEFAULT_COLOR);
    expect(result).toBe(DEFAULT_COLOR);
  });
  it("returns the default color when advisory threshold is not met", () => {
    const result = calculateStatusColour(fireShapeDetails, 80, DEFAULT_COLOR);
    expect(result).toBe(DEFAULT_COLOR);
  });
  it("returns advisory color when advisory threshold met", () => {
    const result = calculateStatusColour(fireShapeDetails, 38, DEFAULT_COLOR);
    expect(result).toBe(ADVISORY_ORANGE_FILL);
  });
  it("returns warning color when warning threshold met", () => {
    const result = calculateStatusColour(fireShapeDetails, 16, DEFAULT_COLOR);
    expect(result).toBe(ADVISORY_RED_FILL);
  });
});

describe("calculateStatusText", () => {
  it("returns undefined when FireShapeAreaDetail array is empty", () => {
    const result = calculateStatusText([], 20);
    expect(result).toBe(undefined);
  });
  it("returns undefined when advisory threshold is not met", () => {
    const result = calculateStatusText(fireShapeDetails, 80);
    expect(result).toBe(undefined);
  });
  it("returns advisory status when advisory threshold is met", () => {
    const result = calculateStatusText(fireShapeDetails, 38);
    expect(result).toBe(AdvisoryStatus.ADVISORY);
  });
  it("returns warning status when warning threshold is met", () => {
    const result = calculateStatusText(fireShapeDetails, 16);
    expect(result).toBe(AdvisoryStatus.WARNING);
  });
});

describe("getWindSpeedMinimum", () => {
  it("returns the lower of two valid wind speeds", () => {
    const input: AdvisoryMinWindStats[] = [
      { threshold: advisoryThreshold, min_wind_speed: 12 },
      { threshold: warningThreshold, min_wind_speed: 8 },
    ];
    expect(getWindSpeedMinimum(input)).toBe(8);
  });

  it("returns the advisory wind speed if warning is missing", () => {
    const input: AdvisoryMinWindStats[] = [
      { threshold: advisoryThreshold, min_wind_speed: 10 },
    ];
    expect(getWindSpeedMinimum(input)).toBe(10);
  });

  it("returns the warning wind speed if advisory is missing", () => {
    const input: AdvisoryMinWindStats[] = [
      { threshold: warningThreshold, min_wind_speed: 7 },
    ];
    expect(getWindSpeedMinimum(input)).toBe(7);
  });

  it("ignores wind speeds < 0", () => {
    const input: AdvisoryMinWindStats[] = [
      { threshold: advisoryThreshold, min_wind_speed: 0 },
      { threshold: warningThreshold, min_wind_speed: -5 },
    ];
    expect(getWindSpeedMinimum(input)).toBe(0);
  });

  it("returns undefined if both min_wind_speed values are missing", () => {
    const input: AdvisoryMinWindStats[] = [
      { threshold: advisoryThreshold },
      { threshold: warningThreshold },
    ];
    expect(getWindSpeedMinimum(input)).toBeUndefined();
  });

  it("returns undefined if input array is empty", () => {
    expect(getWindSpeedMinimum([])).toBeUndefined();
  });
});

describe("calculateWindSpeedText", () => {
  it.each([
    {
      description:
        "return the correct wind speed string for the minimum wind speed",
      input: [
        { threshold: advisoryThreshold, min_wind_speed: 12 },
        { threshold: warningThreshold, min_wind_speed: 15 },
      ],
      expected: "if winds exceed 12 km/h",
    },
    {
      description:
        "return the correct wind speed string if a valid wind speed is present",
      input: [
        { threshold: advisoryThreshold, min_wind_speed: -5 },
        { threshold: warningThreshold, min_wind_speed: 0 },
      ],
      expected: "if winds exceed 0 km/h",
    },
  ])("should $description", ({ input, expected }) => {
    const windText = calculateWindSpeedText(input);
    expect(windText).toBe(expected);
  });
  it("should return undefined if there are no valid wind speeds", () => {
    const input: AdvisoryMinWindStats[] = [
      { threshold: advisoryThreshold, min_wind_speed: -5 },
    ];
    const windText = calculateWindSpeedText(input);
    expect(windText).toBeUndefined();
  });
});
