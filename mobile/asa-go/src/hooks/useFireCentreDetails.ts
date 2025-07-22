import { selectProvincialSummary } from "@/slices/provincialSummarySlice";
import { FireCenter, FireShapeAreaDetail } from "api/fbaAPI";
import { groupBy } from "lodash";
import { useMemo } from "react";
import { useSelector } from "react-redux";

export interface GroupedFireZoneUnitDetails {
  fire_shape_id: number;
  fire_shape_name: string;
  fire_centre_name: string;
  fireShapeDetails: FireShapeAreaDetail[];
}

/**
 * Hook for grabbing a fire centre from the provincial summary, grouping by unique 'fire_shape_id' and
 * providing easy access to the shape name, centre, and FireShapeAreaDetails for calculating zone status
 *
 * @param selectedFireCenter
 * @returns
 */
export const useFireCentreDetails = (
  selectedFireCenter: FireCenter | undefined
): GroupedFireZoneUnitDetails[] => {
  const provincialSummary = useSelector(selectProvincialSummary);

  return useMemo(() => {
    if (!selectedFireCenter) return [];

    const fireCenterSummary = provincialSummary[selectedFireCenter.name] || [];
    const groupedFireZoneUnits = groupBy(fireCenterSummary, "fire_shape_id");

    return Object.values(groupedFireZoneUnits)
      .map((group) => ({
        fire_shape_id: group[0].fire_shape_id,
        fire_shape_name: group[0].fire_shape_name,
        fire_centre_name: group[0].fire_centre_name,
        fireShapeDetails: group,
      }))
      .sort((a, b) => a.fire_shape_name.localeCompare(b.fire_shape_name));
  }, [selectedFireCenter, provincialSummary]);
};
