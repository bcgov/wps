import { useMemo } from 'react'
import { useSelector } from 'react-redux'
import { FireCenter, FireShapeStatusDetail } from 'api/fbaAPI'
import { selectProvincialSummary } from 'features/fba/slices/provincialSummarySlice'

/**
 * Hook for grabbing a fire centre from the provincial summary, grouping by unique 'fire_shape_id' and
 * providing easy access to the shape name, centre, and FireShapeStatusDetails for calculating zone status
 *
 * @param selectedFireCenter
 * @returns
 */
export const useFireCentreDetails = (selectedFireCenter: FireCenter | undefined): FireShapeStatusDetail[] => {
  const provincialSummary = useSelector(selectProvincialSummary)

  return useMemo(() => {
    if (!selectedFireCenter) return []

    const fireCenterSummary = provincialSummary[selectedFireCenter.name] || []

    return fireCenterSummary.sort((a, b) => a.fire_shape_name.localeCompare(b.fire_shape_name))
  }, [selectedFireCenter, provincialSummary])
}
