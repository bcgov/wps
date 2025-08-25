import { FireZoneTPIStats } from "@/api/fbaAPI";
import { selectTPIStats } from "@/store";
import { isNil } from "lodash";
import { DateTime } from "luxon";
import { useMemo } from "react";
import { useSelector } from "react-redux";

/**
 * A hook for retrieving the FireZoneTPIStats for the provided forDate.
 * @param forDate
 * @returns FireZoneTPIStats[]
 */
export const useTPIStatsForDate = (forDate: DateTime): FireZoneTPIStats[] => {
  const tpiStats = useSelector(selectTPIStats);
  return useMemo(() => {
    const forDateString = forDate.toISODate();
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
