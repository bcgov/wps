import { FireShapeArea } from "@/api/fbaAPI";
import { selectFireShapeAreas } from "@/store";
import { isNil } from "lodash";
import { DateTime } from "luxon";
import { useMemo } from "react";
import { useSelector } from "react-redux";

/**
 * A hook for retrieving the FireShapeAreas for the provided forDate.
 * @param forDate
 * @returns FireShapeArea[]
 */
export const useFireShapeAreasForDate = (
  forDate: DateTime
): FireShapeArea[] => {
  const fireShapeAreas = useSelector(selectFireShapeAreas);
  return useMemo(() => {
    const forDateString = forDate.toISODate();
    if (
      isNil(forDate) ||
      isNil(forDateString) ||
      isNil(fireShapeAreas?.[forDateString]?.data)
    ) {
      return [];
    }
    const fireShapeAreasForDate = fireShapeAreas[forDateString].data;
    return fireShapeAreasForDate;
  }, [fireShapeAreas, forDate]);
};
