import * as React from 'react'
import { FuelType, PlanningArea } from 'api/hfiCalculatorAPI'
import { sortBy } from 'lodash'
import PlanningAreaAdmin from 'features/hfiCalculator/components/stationAdmin/PlanningAreaAdmin'
import { Box } from '@mui/material'
import { AddStationOptions } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { StationInfo } from 'features/hfiCalculator/slices/hfiCalculatorSlice'

export interface StationListAdminProps {
  planningAreas: PlanningArea[]
  fuelTypes: FuelType[]
  addStationOptions?: AddStationOptions
  planningAreaStationInfo: { [key: number]: StationInfo[] }
}

const StationListAdmin = ({
  planningAreas,
  planningAreaStationInfo,
  fuelTypes,
  addStationOptions
}: StationListAdminProps) => {
  return (
    <Box sx={{ width: '100%', pl: 4 }} aria-labelledby="planning-areas-admin">
      {sortBy(planningAreas, planningArea => planningArea.order_of_appearance_in_list).map((area, index) => (
        <PlanningAreaAdmin
          key={`planning-area-admin-${index}`}
          planningArea={area}
          fuelTypes={fuelTypes}
          planningAreaStationInfo={planningAreaStationInfo}
          addStationOptions={addStationOptions}
        />
      ))}
    </Box>
  )
}

export default React.memo(StationListAdmin)
