import React from 'react'
import { PlanningArea } from 'api/hfiCalculatorAPI'
import { Button, Typography, Box } from '@mui/material'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import StationForm from 'features/hfiCalculator/components/stationAdmin/StationForm'
import { AddStationOptions } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { sortBy } from 'lodash'

export interface PlanningAreaAdminProps {
  planningArea: PlanningArea
  addStationOptions?: AddStationOptions
}

const PlanningAreaAdmin = ({ planningArea, addStationOptions }: PlanningAreaAdminProps) => {
  return (
    <Box sx={{ width: '100%', pt: 4 }}>
      <Typography variant="h6">
        {planningArea.name}
        <Button variant="text" color="primary" data-testid={'add-station-'}>
          <AddCircleOutlineIcon />
        </Button>
      </Typography>

      {sortBy(planningArea.stations, station => station.order_of_appearance_in_planning_area_list).map(
        (station, idx) => (
          <StationForm key={`pa-admin-station-${idx}`} station={station} addStationOptions={addStationOptions} />
        )
      )}
    </Box>
  )
}

export default React.memo(PlanningAreaAdmin)
