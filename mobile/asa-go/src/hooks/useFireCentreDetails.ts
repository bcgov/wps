import { useProvincialSummaryForDate } from "@/hooks/dataHooks";
import { FireShapeStatusDetail } from "api/fbaAPI";
import type { FireCentre } from "@wps/types/fireCentre";
import { DateTime } from "luxon";
import { useMemo } from "react";

/**
 * Hook for grabbing a fire centre from the provincial summary, grouping by unique 'fire_shape_id' and
 * providing easy access to the shape name, centre, and FireShapeStatusDetails for calculating zone status
 *
 * @param selectedFireCenter
 * @returns
 */
export const useFireCentreDetails = (
  selectedFireCenter: FireCentre | undefined,
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
