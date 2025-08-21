import { FireShapeAreaDetail } from "@/api/fbaAPI";
import { selectProvincialSummaries } from "@/store";
import { Dictionary, groupBy, isNil } from "lodash";
import { DateTime } from "luxon";
import { useMemo } from "react";
import { useSelector } from "react-redux";

/**
 * A hook for retrieving the provincial summary for the provided forDate.
 * @param forDate 
 * @returns FireShapeAreDetail[]
 */
export const useProvincialSummaryForDate = (
  forDate: DateTime
): Dictionary<FireShapeAreaDetail[]> | undefined  => {
  const provincialSummaries = useSelector(selectProvincialSummaries);
  return useMemo(() => {
    const forDateString = forDate.toISODate()
    if (isNil(forDate) || isNil(forDateString) || isNil(provincialSummaries?.[forDateString]?.data)) {
        return undefined;
    }
    const provincialSummary =  provincialSummaries[forDateString].data
    return groupBy(provincialSummary, "fire_centre_name")
  }, [provincialSummaries, forDate]);
};