import React from 'react'
import { PlanningArea } from 'api/hfiCalculatorAPI'
import { Typography, Box, IconButton } from '@mui/material'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import StationForm from 'features/hfiCalculator/components/stationAdmin/StationForm'
import { AddStationOptions, StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { AdminHandlers } from 'features/hfiCalculator/components/stationAdmin/StationListAdmin'

export interface PlanningAreaAdminProps {
  planningArea: Pick<PlanningArea, 'id' | 'name'>
  planningAreaAdminStations: { [key: string]: StationAdminRow[] }
  addStationOptions?: AddStationOptions
  adminHandlers: AdminHandlers
}

const PlanningAreaAdmin = ({
  planningArea,
  addStationOptions,
  adminHandlers,
  planningAreaAdminStations
}: PlanningAreaAdminProps) => {
  const stationAdminRow = planningAreaAdminStations[planningArea.id]
  return (
    <Box sx={{ width: '100%', pt: 4 }} data-testid="planning-area-admin">
      <Typography variant="h6">
        {planningArea.name}
        <IconButton
          data-testid="admin-add-station-button"
          color="primary"
          size="large"
          onClick={() => {
            adminHandlers.handleAddStation(planningArea.id)
          }}
        >
          <AddCircleOutlineIcon />
        </IconButton>
      </Typography>

      {stationAdminRow.map(adminRow => {
        return (
          <StationForm
            key={`pa-admin-station-${planningArea.id}-${adminRow.rowId}`}
            adminRow={adminRow}
            planningAreaId={planningArea.id}
            addStationOptions={addStationOptions}
            adminHandlers={adminHandlers}
          />
        )
      })}
    </Box>
  )
}

export default React.memo(PlanningAreaAdmin)
