import { useProvincialSummaryForDate } from "@/hooks/dataHooks";
import { FireCenter, FireShapeStatusDetail } from "api/fbaAPI";
import { DateTime } from "luxon";
import { useMemo } from "react";

/**
 * Hook for grabbing a fire centre from the provincial summary, grouping by unique 'fire_shape_id' and
 * providing easy access to the shape name, centre, and FireShapeAreaDetails for calculating zone status
 *
 * @param selectedFireCenter
 * @returns
 */
export const useFireCentreDetails = (
  selectedFireCenter: FireCenter | undefined,
  forDate: DateTime
): FireShapeStatusDetail[] => {
  const provincialSummary = useProvincialSummaryForDate(forDate);

  return useMemo(() => {
    if (!selectedFireCenter) return [];

    const fireCenterSummary =
      provincialSummary?.[selectedFireCenter.name] || [];

    return fireCenterSummary.sort((a, b) =>
      a.fire_shape_name.localeCompare(b.fire_shape_name)
    );
  }, [selectedFireCenter, provincialSummary]);
};
