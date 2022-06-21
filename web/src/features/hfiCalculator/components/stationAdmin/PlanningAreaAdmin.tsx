import React from 'react'
import { FuelType, PlanningArea } from 'api/hfiCalculatorAPI'
import { Button, Typography, Box } from '@mui/material'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import StationForm from 'features/hfiCalculator/components/stationAdmin/StationForm'
import { AddStationOptions } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { sortBy } from 'lodash'
import { StationInfo } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { getSelectedFuelType } from 'features/hfiCalculator/util'

export interface PlanningAreaAdminProps {
  planningArea: PlanningArea
  planningAreaStationInfo: { [key: number]: StationInfo[] }
  fuelTypes: FuelType[]
  addStationOptions?: AddStationOptions
}

const PlanningAreaAdmin = ({
  planningArea,
  planningAreaStationInfo,
  fuelTypes,
  addStationOptions
}: PlanningAreaAdminProps) => {
  return (
    <Box sx={{ width: '100%', pt: 4 }}>
      <Typography variant="h6">
        {planningArea.name}
        <Button variant="text" color="primary" data-testid={'add-station-'}>
          <AddCircleOutlineIcon />
        </Button>
      </Typography>

      {sortBy(planningArea.stations, station => station.order_of_appearance_in_planning_area_list).map(
        (station, idx) => {
          const fuelType = getSelectedFuelType(planningAreaStationInfo, planningArea.id, station.code, fuelTypes)
          return (
            <StationForm
              key={`pa-admin-station-${idx}`}
              adminRow={{
                planningAreaId: planningArea.id,
                station: { code: station.code, name: station.station_props.name },
                fuelType
              }}
              rowId={idx}
              planningAreaId={planningArea.id}
              addStationOptions={addStationOptions}
            />
          )
        }
      )}
    </Box>
  )
}

export default React.memo(PlanningAreaAdmin)
