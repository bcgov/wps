import React from 'react'
import { PlanningArea } from 'api/hfiCalculatorAPI'
import { Typography, Box, IconButton } from '@mui/material'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import ExistingStationList from 'features/hfiCalculator/components/stationAdmin/ExistingStationList'
import { AddStationOptions, StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { AdminHandlers } from 'features/hfiCalculator/components/stationAdmin/StationListAdmin'
import NewStationList from 'features/hfiCalculator/components/stationAdmin/NewStationList'
import { differenceWith, isEqual } from 'lodash'

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
          <AddCircleOutlineIcon />
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
