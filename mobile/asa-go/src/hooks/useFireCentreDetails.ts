import { useProvincialSummaryForDate } from "@/hooks/dataHooks";
import { FireShapeStatusDetail } from "api/fbaAPI";
import type { FireCentre } from "@/types/fireCentre";
import { DateTime } from "luxon";
import { useMemo } from "react";

/**
 * Hook for grabbing a fire centre from the provincial summary, grouping by unique 'fire_shape_id' and
 * providing easy access to the shape name, centre, and FireShapeStatusDetails for calculating zone status
 *
 * @param selectedFireCentre
 * @returns
 */
export const useFireCentreDetails = (
  selectedFireCentre: FireCentre | undefined,
  forDate: DateTime,
): FireShapeStatusDetail[] => {
  const provincialSummary = useProvincialSummaryForDate(forDate);

  return useMemo(() => {
    if (!selectedFireCentre) return [];

    const fireCentreSummary =
      provincialSummary?.[selectedFireCentre.name] || [];

    return fireCentreSummary.sort((a, b) =>
      a.fire_shape_name.localeCompare(b.fire_shape_name),
    );
  }, [selectedFireCentre, provincialSummary]);
};
