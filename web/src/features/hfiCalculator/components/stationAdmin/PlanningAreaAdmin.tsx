import React from 'react'
import { PlanningArea } from 'api/hfiCalculatorAPI'
import { Typography, Box, IconButton } from '@mui/material'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import StationForm from 'features/hfiCalculator/components/stationAdmin/StationForm'
import { AddStationOptions } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { StationAdminRow } from 'features/hfiCalculator/stationAdmin/admin'
import { AdminHandlers } from 'features/hfiCalculator/components/stationAdmin/StationListAdmin'

export interface PlanningAreaAdminProps {
  planningArea: PlanningArea
  adminRows: { [key: string]: StationAdminRow[] }
  addStationOptions?: AddStationOptions
  adminHandlers: AdminHandlers
}

const PlanningAreaAdmin = ({ planningArea, addStationOptions, adminHandlers, adminRows }: PlanningAreaAdminProps) => {
  const stationAdminRow = adminRows[planningArea.id]
  return (
    <Box sx={{ width: '100%', pt: 4 }}>
      <Typography variant="h6">
        {planningArea.name}
        <IconButton
          color="primary"
          size="large"
          onClick={() => {
            adminHandlers.handleAddStation(planningArea.id)
          }}
        >
          <AddCircleOutlineIcon />
        </IconButton>
        {/* <Button variant="text" color="primary" data-testid={'add-station-'}>
          <AddCircleOutlineIcon />
        </Button> */}
      </Typography>

      {stationAdminRow.map((adminRow, idx) => {
        return (
          <StationForm
            key={`pa-admin-station-${idx}`}
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
