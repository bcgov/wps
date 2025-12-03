import { useMemo } from 'react'
import { useSelector } from 'react-redux'
import { FireCenter, FireShapeAreaDetail } from 'api/fbaAPI'
import { selectProvincialSummary } from 'features/fba/slices/provincialSummarySlice'

export interface GroupedFireZoneUnitDetails {
  fire_shape_id: number
  fire_shape_name: string
  fire_centre_name: string
  fireShapeDetails: FireShapeAreaDetail[]
}

/**
 * Hook for grabbing a fire centre from the provincial summary, grouping by unique 'fire_shape_id' and
 * providing easy access to the shape name, centre, and FireShapeAreaDetails for calculating zone status
 *
 * @param selectedFireCenter
 * @returns
 */
export const useFireCentreDetails = (selectedFireCenter: FireCenter | undefined): FireShapeAreaDetail[] => {
  const provincialSummary = useSelector(selectProvincialSummary)

  return useMemo(() => {
    if (!selectedFireCenter) return []

    const fireCenterSummary = provincialSummary[selectedFireCenter.name] || []

    return fireCenterSummary.sort((a, b) => a.fire_shape_name.localeCompare(b.fire_shape_name))
  }, [selectedFireCenter, provincialSummary])
}
