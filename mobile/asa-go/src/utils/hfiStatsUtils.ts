import {
  FireZoneFuelStats,
  FireZoneHFIStatsDictionary,
} from "@/api/fbaAPI";

// Based on 100 pixels at a 2000m resolution fuel raster measured in square meters.
export const FUEL_AREA_THRESHOLD = 100 * 2000 * 2000;
const FUEL_TYPES_ALWAYS_INCLUDED = ["C-5", "S-1", "S-2", "S-3"];

/**
 * Filters out fuel types which cover less than 100 pixels at a 2km resolution but always includes
 * all slash fuel types and C5 regardless of their spatial coverage with respect to high HFI area.
 * @returns FireCentreHFIStats with low prevalence fuel types filtered out.
 */
export const filterHFIFuelStatsByArea = (
  fireCentreHFIFuelStats: FireZoneHFIStatsDictionary
) => {
  const filteredFireZoneStats: FireZoneHFIStatsDictionary = {};
    for (const [key, value] of Object.entries(fireCentreHFIFuelStats)) {
      filteredFireZoneStats[parseInt(key)] = {
        min_wind_stats: value.min_wind_stats,
        fuel_area_stats: filterHFIStatsByArea(value.fuel_area_stats),
      };
  }
  return filteredFireZoneStats;
};

/**
 * Filters out FireZoneFuelStats that do not meet the area threshold but always includes
 * slash and C-5 fuel types regardless of their prevalence.
 * @param stats The FireZoneFuelStats to filter.
 * @returns An array of filtered FireZoneFuelStats.
 */
const filterHFIStatsByArea = (stats: FireZoneFuelStats[]) => {
  return stats.filter(
    (stat) =>
      stat.fuel_area > FUEL_AREA_THRESHOLD ||
      FUEL_TYPES_ALWAYS_INCLUDED.includes(stat.fuel_type.fuel_type_code)
  );
};
