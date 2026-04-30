import {
  FireShapeStatusDetail,
  FireZoneHFIStatsDictionary,
  FireZoneTPIStats,
} from "@/api/fbaAPI";
import {
  selectHFIStats,
  selectProvincialSummaries,
  selectTPIStats,
} from "@/store";
import { filterHFIFuelStatsByArea } from "@/utils/hfiStatsUtils";
import { Dictionary, groupBy, isNil } from "lodash";
import { DateTime } from "luxon";
import { useMemo } from "react";
import { useSelector } from "react-redux";

/**
 * A hook for retrieving the FireZoneHFIStatsDictionary for the provided forDate.
 * @param forDate
 * @returns FireZoneHFIStatsDictionary]
 */
export const useFilteredHFIStatsForDate = (
  forDate: DateTime
): FireZoneHFIStatsDictionary => {
  const hfiStats = useSelector(selectHFIStats);
  return useMemo(() => {
    const forDateString = forDate?.toISODate();
    if (
      isNil(forDate) ||
      isNil(forDateString) ||
      isNil(hfiStats?.[forDateString]?.data)
    ) {
      return [];
    }
    const hfiStatsForDate = hfiStats[forDateString].data;
    const filteredHFIStatsForDate = filterHFIFuelStatsByArea(hfiStatsForDate);
    return filteredHFIStatsForDate;
  }, [hfiStats, forDate]);
};

/**
 * A hook for retrieving the provincial summary for the provided forDate.
 * @param forDate
 * @returns Dictionary<FireShapeStatusDetail[]> | undefined
 */
export const useProvincialSummaryForDate = (
  forDate: DateTime
): Dictionary<FireShapeStatusDetail[]> | undefined => {
  const provincialSummaries = useSelector(selectProvincialSummaries);
  return useMemo(() => {
    const forDateString = forDate?.toISODate();
    if (
      isNil(forDate) ||
      isNil(forDateString) ||
      isNil(provincialSummaries?.[forDateString]?.data)
    ) {
      return undefined;
    }
    const provincialSummary = provincialSummaries[forDateString].data;
    return groupBy(provincialSummary, "fire_centre_name");
  }, [provincialSummaries, forDate]);
};

/**
 * A hook for retrieving the provincial summary for the provided forDate.
 * @param forDate
 * @returns FireShapeStatusDetail[] | undefined
 */
export const useProvincialSummaryZonesForDate = (
  forDate: DateTime
): FireShapeStatusDetail[] | undefined => {
  const provincialSummaries = useSelector(selectProvincialSummaries);
  return useMemo(() => {
    const forDateString = forDate?.toISODate();
    if (
      isNil(forDate) ||
      isNil(forDateString) ||
      isNil(provincialSummaries?.[forDateString]?.data)
    ) {
      return undefined;
    }
    const provincialSummary = provincialSummaries[forDateString].data;
    return provincialSummary;
  }, [provincialSummaries, forDate]);
};

/**
 * A hook for retrieving the FireZoneTPIStats for the provided forDate.
 * @param forDate
 * @returns FireZoneTPIStats[]
 */
export const useTPIStatsForDate = (forDate: DateTime): FireZoneTPIStats[] => {
  const tpiStats = useSelector(selectTPIStats);
  return useMemo(() => {
    const forDateString = forDate?.toISODate();
    if (
      isNil(forDate) ||
      isNil(forDateString) ||
      isNil(tpiStats?.[forDateString]?.data)
    ) {
      return [];
    }
    const tpiStatsForDate = tpiStats[forDateString].data;
    return tpiStatsForDate;
  }, [tpiStats, forDate]);
};
