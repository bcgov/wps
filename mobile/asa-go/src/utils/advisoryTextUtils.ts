import {
  AdvisoryMinWindStats,
  FireZoneFuelStats,
  FireZoneHFIStats,
} from "@/api/fbaAPI";
import { calculateWindSpeedText } from "@/utils/calculateZoneStatus";
import { groupBy, isEmpty } from "lodash";
import { DateTime } from "luxon";

const SLASH_FUEL_TYPES = ["S-1", "S-2", "S-3"];

// Return a list of fuel stats for which greater than 90% of the area of each fuel type has high HFI.
export const getTopFuelsByProportion = (
  zoneUnitFuelStats: FireZoneFuelStats[]
): FireZoneFuelStats[] => {
  const groupedByFuelType = groupBy(
    zoneUnitFuelStats,
    (stat) => stat.fuel_type.fuel_type_code
  );
  const topFuelsByProportion: FireZoneFuelStats[] = [];

  Object.values(groupedByFuelType).forEach((entries) => {
    const totalArea = entries.reduce((sum, entry) => sum + entry.area, 0);
    const fuelArea = entries[0].fuel_area;
    if (totalArea / fuelArea >= 0.9) {
      topFuelsByProportion.push(...entries);
    }
  });
  return topFuelsByProportion;
};

/**
 * Determine if we are in the core season ie between June 1 - September 30. Alternate logic for
 * handling slash fuel types in the advisory text is required during this period.
 * @param date
 * @returns True if the date is between June 1 - September 30, otherwise False.
 */
const isCoreSeason = (date: DateTime) => {
  return date.month > 5 && date.month < 10;
};

/**
 * Returns the fuel type stat records that cumulatively account for more than 75% of total area with high HFI.
 * The zoneUnitFuelStats may contain more than 1 record for each fuel type, if there are pixels matching both
 * HFI class 5 and 6 for that fuel type. From June 1 - September 30 slash fuel types (S-1, S-2 and S-3) are
 * not used as a top fuel type.
 * @param zoneUnitFuelStats
 * @returns FireZoneFuelStats array
 */
export const getTopFuelsByArea = (
  zoneUnitFuelStats: FireZoneHFIStats,
  forDate: DateTime
): FireZoneFuelStats[] => {
  let fuelAreaStats = zoneUnitFuelStats.fuel_area_stats;
  if (isCoreSeason(forDate)) {
    fuelAreaStats = fuelAreaStats.filter(
      (stat) => !SLASH_FUEL_TYPES.includes(stat.fuel_type.fuel_type_code)
    );
  }

  const groupedByFuelType = groupBy(
    fuelAreaStats,
    (stat) => stat.fuel_type.fuel_type_code
  );
  const fuelTypeAreas = Object.entries(groupedByFuelType).map(
    ([fuelType, entries]) => ({
      fuelType,
      fuelTypeTotalHfi: entries.reduce((sum, entry) => sum + entry.area, 0),
      entries,
    })
  );
  const sortedFuelTypes = fuelTypeAreas
    .slice()
    .sort((a, b) => b.fuelTypeTotalHfi - a.fuelTypeTotalHfi);
  const totalHighHFIArea = fuelAreaStats.reduce(
    (total, stats) => total + stats.area,
    0
  );
  const topFuelsByArea: FireZoneFuelStats[] = [];
  let highHFIArea = 0;

  for (const { fuelTypeTotalHfi, entries } of sortedFuelTypes) {
    highHFIArea += fuelTypeTotalHfi;
    topFuelsByArea.push(...entries);

    if (highHFIArea / totalHighHFIArea > 0.75) {
      break;
    }
  }

  return topFuelsByArea;
};

export const getZoneMinWindStatsText = (
  selectedFireZoneUnitMinWindSpeeds: AdvisoryMinWindStats[]
) => {
  if (!isEmpty(selectedFireZoneUnitMinWindSpeeds)) {
    const zoneMinWindSpeedsText = calculateWindSpeedText(
      selectedFireZoneUnitMinWindSpeeds
    );
    return zoneMinWindSpeedsText;
  }
};
