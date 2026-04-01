import { useMemo } from 'react'
import { useSelector } from 'react-redux'
import { FireShapeStatusDetail } from '@wps/api/fbaAPI'
import type { FireCentre } from '@wps/types/fireCentre'
import { selectProvincialSummary } from 'features/fba/slices/provincialSummarySlice'

/**
 * Hook for grabbing a fire centre from the provincial summary, grouping by unique 'fire_shape_id' and
 * providing easy access to the shape name, centre, and FireShapeStatusDetails for calculating zone status
 *
 * @param selectedFireCentre
 * @returns
 */
export const useFireCentreDetails = (selectedFireCentre: FireCentre | undefined): FireShapeStatusDetail[] => {
  const provincialSummary = useSelector(selectProvincialSummary)

  return useMemo(() => {
    if (!selectedFireCentre) return []

    const fireCentreSummary = provincialSummary[selectedFireCentre.name] || []

    return fireCentreSummary.sort((a, b) => a.fire_shape_name.localeCompare(b.fire_shape_name))
  }, [selectedFireCentre, provincialSummary])
}
