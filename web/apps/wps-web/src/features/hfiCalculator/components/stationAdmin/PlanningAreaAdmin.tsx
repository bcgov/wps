import AddCircleOutlineOutlinedIcon from '@mui/icons-material/AddCircleOutlineOutlined'
import { Box, IconButton, Typography } from '@mui/material'
import type { PlanningArea } from '@wps/api/hfiCalculatorAPI'
import ExistingStationList from 'features/hfiCalculator/components/stationAdmin/ExistingStationList'
import type {
  AddStationOptions,
  StationAdminRow
} from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'
import NewStationList from 'features/hfiCalculator/components/stationAdmin/NewStationList'
import type { AdminHandlers } from 'features/hfiCalculator/components/stationAdmin/StationListAdmin'
import { differenceWith, isEqual } from 'lodash'
import React from 'react'

export interface PlanningAreaAdminProps {
  planningArea: Pick<PlanningArea, 'id' | 'name'>
  existingStations: { [key: string]: StationAdminRow[] }
  addedStations: { [key: string]: StationAdminRow[] }
  removedStations: { [key: string]: StationAdminRow[] }
  addStationOptions?: AddStationOptions
  adminHandlers: AdminHandlers
}

const PlanningAreaAdmin = ({
  planningArea,
  addStationOptions,
  adminHandlers,
  existingStations,
  addedStations,
  removedStations
}: PlanningAreaAdminProps) => {
  const existingStationsRow = existingStations[planningArea.id]
  const removedStationsRow = removedStations[planningArea.id]

  const currentStations = differenceWith(
    existingStationsRow,
    removedStationsRow,
    (a, b) => isEqual(a.planningAreaId, b.planningAreaId) && isEqual(a.rowId, b.rowId)
  )
  const addedStationsRow = addedStations[planningArea.id] ? addedStations[planningArea.id] : []
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
          <AddCircleOutlineOutlinedIcon />
        </IconButton>
      </Typography>

      {currentStations.map(adminRow => {
        return (
          <ExistingStationList
            key={`existing-admin-station-${planningArea.id}-${adminRow.rowId}`}
            adminRow={adminRow}
            planningAreaId={planningArea.id}
            addStationOptions={addStationOptions}
            adminHandlers={adminHandlers}
          />
        )
      })}
      {addedStationsRow.map(added => {
        return (
          <NewStationList
            key={`added-station-list-${planningArea.id}-${added.rowId}`}
            newStation={added}
            planningAreaId={planningArea.id}
            addStationOptions={addStationOptions}
            handleRemoveStation={adminHandlers.handleRemoveStation}
            handleEditStation={adminHandlers.handleEditStation}
          />
        )
      })}
    </Box>
  )
}

export default React.memo(PlanningAreaAdmin)
