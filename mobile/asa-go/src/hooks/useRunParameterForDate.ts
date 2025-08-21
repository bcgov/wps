import { RunParameter } from "@/api/fbaAPI";
import { selectRunParameters } from "@/store";
import { isNil } from "lodash";
import { DateTime } from "luxon";
import { useMemo } from "react";
import { useSelector } from "react-redux";

/**
 * A hook for retrieving the run parameters for the provided forDate.
 * @param forDate 
 * @returns 
 */
export const useRunParameterForDate = (
  forDate: DateTime
): RunParameter | undefined => {
  const runParameters = useSelector(selectRunParameters);
  return useMemo(() => {
    const forDateString = forDate.toISODate()
    if (isNil(forDate) || isNil(forDateString) || isNil(runParameters)) {
        return undefined;
    }
    return runParameters[forDateString]
  }, [runParameters, forDate]);
};