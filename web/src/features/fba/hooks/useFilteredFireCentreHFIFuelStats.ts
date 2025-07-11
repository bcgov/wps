import { useSelector } from 'react-redux'
import { selectFireCentreHFIFuelStats } from '@/app/rootReducer'
import { FireCentreHFIStats } from '@/api/fbaAPI'
import { filterHFIFuelStatsByArea } from '@/features/fba/hfiStatsUtils'

export const useFilteredFireCentreHFIFuelStats = (): FireCentreHFIStats => {
  const { fireCentreHFIFuelStats } = useSelector(selectFireCentreHFIFuelStats)

  return filterHFIFuelStatsByArea(fireCentreHFIFuelStats)
}
