import { Alert, Box } from '@mui/material'
import type { FuelType, PlanningArea } from '@wps/api/hfiCalculatorAPI'
import type { AppDispatch } from 'app/store'
import AdminCancelButton from 'features/hfiCalculator/components/stationAdmin/AdminCancelButton'
import type {
  AddStationOptions,
  BasicWFWXStation,
  StationAdminRow
} from 'features/hfiCalculator/components/stationAdmin/ManageStationsModal'
import PlanningAreaAdmin from 'features/hfiCalculator/components/stationAdmin/PlanningAreaAdmin'
import SaveStationUpdatesButton from 'features/hfiCalculator/components/stationAdmin/SaveStationUpdatesButton'
import { fetchAddOrUpdateStations } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { every, isUndefined, maxBy, sortBy } from 'lodash'
import React, { useState } from 'react'
import { useDispatch } from 'react-redux'

export interface AdminHandlers {
  handleRemoveExistingStation: (planningAreaId: number, rowId: number, station: BasicWFWXStation) => void
  /** Net new station handlers */
  handleAddStation: (planningAreaId: number) => void
  handleRemoveStation: (planningAreaId: number, rowId: number) => void
  handleEditStation: (planningAreaId: number, rowId: number, station: StationAdminRow) => void
}

export interface StationListAdminProps {
  fireCentreId: number
  planningAreas: PlanningArea[]
  fuelTypes: Pick<FuelType, 'id' | 'abbrev'>[]
  addStationOptions?: AddStationOptions
  existingPlanningAreaStations: { [key: string]: StationAdminRow[] }
  stationUpdateError?: string | null
  handleClose: () => void
}

const StationListAdmin = ({
  fireCentreId,
  planningAreas,
  addStationOptions,
  existingPlanningAreaStations,
  stationUpdateError,
  handleClose
}: StationListAdminProps) => {
  const dispatch: AppDispatch = useDispatch()

  const emptyRowsByPlanningArea = Object.fromEntries(planningAreas.map(planningArea => [planningArea.id, []]))
  const [addedStations, setAddedStations] = useState<{ [key: string]: StationAdminRow[] }>(emptyRowsByPlanningArea)
  const [removedStations, setRemovedStations] = useState<{
    [key: string]: { planningAreaId: number; rowId: number; station: BasicWFWXStation }[]
  }>(emptyRowsByPlanningArea)

  /** Adds net new stations */
  const handleAddStation = (planningAreaId: number) => {
    const currentRows = addedStations[planningAreaId] ?? []
    const maxRowId = maxBy(currentRows, 'rowId')?.rowId
    const lastRowId = maxRowId ? maxRowId : 0
    setAddedStations({
      ...addedStations,
      [planningAreaId]: currentRows.concat([{ planningAreaId, rowId: lastRowId + 1 }])
    })
  }

  /** Removes net new stations */
  const handleRemoveStation = (planningAreaId: number, rowId: number) => {
    setAddedStations({
      ...addedStations,
      [planningAreaId]: (addedStations[planningAreaId] ?? []).filter(row => row.rowId !== rowId)
    })
  }

  /** Edits net new stations */
  const handleEditStation = (planningAreaId: number, rowId: number, row: StationAdminRow) => {
    setAddedStations({
      ...addedStations,
      [planningAreaId]: (addedStations[planningAreaId] ?? []).map(currentRow =>
        currentRow.rowId === rowId ? row : currentRow
      )
    })
  }

  /** Removes existing stations, not net new ones */
  const handleRemoveExistingStation = (planningAreaId: number, rowId: number, station: BasicWFWXStation) => {
    const currentRows = removedStations[planningAreaId] ?? []
    setRemovedStations({
      ...removedStations,
      [planningAreaId]: currentRows.concat({ planningAreaId, rowId, station })
    })
  }

  const handleSave = async () => {
    const allAdded = Object.values(addedStations).flat()
    const allRemoved = Object.values(removedStations).flat()
    if (every(allAdded, addedStation => !isUndefined(addedStation.station) && !isUndefined(addedStation.fuelType))) {
      const saved = await dispatch(
        fetchAddOrUpdateStations(
          fireCentreId,
          allAdded as Required<StationAdminRow>[],
          allRemoved as Required<Pick<StationAdminRow, 'planningAreaId' | 'rowId' | 'station'>>[]
        )
      )
      if (saved) {
        handleClose()
      }
    }
  }

  return (
    <Box sx={{ width: '100%', pl: 4 }} aria-labelledby="planning-areas-admin">
      {stationUpdateError && (
        <Alert severity="error" sx={{ mb: 2, mr: 4 }} data-testid="station-update-error">
          {stationUpdateError}
        </Alert>
      )}
      {sortBy(planningAreas, planningArea => planningArea.order_of_appearance_in_list).map(area => (
        <PlanningAreaAdmin
          key={`planning-area-admin-${area.id}`}
          planningArea={area}
          existingStations={existingPlanningAreaStations}
          addedStations={addedStations}
          removedStations={removedStations}
          addStationOptions={addStationOptions}
          adminHandlers={{
            handleAddStation,
            handleRemoveStation,
            handleEditStation,
            handleRemoveExistingStation
          }}
        />
      ))}
      <SaveStationUpdatesButton
        addedStations={Object.values(addedStations).flat()}
        removedStations={Object.values(removedStations).flat()}
        handleSave={handleSave}
      />
      <AdminCancelButton handleCancel={handleClose} />
    </Box>
  )
}

export default React.memo(StationListAdmin)
