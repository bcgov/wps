import { Box } from '@mui/material'
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
import { every, findIndex, isUndefined, maxBy, sortBy } from 'lodash'
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
  handleClose: () => void
}

const StationListAdmin = ({
  fireCentreId,
  planningAreas,
  addStationOptions,
  existingPlanningAreaStations,
  handleClose
}: StationListAdminProps) => {
  const dispatch: AppDispatch = useDispatch()

  const [addedStations, setAddedStations] = useState<{ [key: string]: StationAdminRow[] }>(
    Object.fromEntries(Object.keys(existingPlanningAreaStations).map(key => [key, []]))
  )
  const [removedStations, setRemovedStations] = useState<{
    [key: string]: { planningAreaId: number; rowId: number; station: BasicWFWXStation }[]
  }>(Object.fromEntries(Object.keys(existingPlanningAreaStations).map(key => [key, []])))

  /** Adds net new stations */
  const handleAddStation = (planningAreaId: number) => {
    const maxRowId = maxBy(addedStations[planningAreaId], 'rowId')?.rowId
    const lastRowId = maxRowId ? maxRowId : 0
    const currentRow = addedStations[planningAreaId].concat([{ planningAreaId, rowId: lastRowId + 1 }])
    setAddedStations({
      ...addedStations,
      [planningAreaId]: currentRow
    })
  }

  /** Removes net new stations */
  const handleRemoveStation = (planningAreaId: number, rowId: number) => {
    const currentlyAdded = addedStations[planningAreaId]
    const idx = findIndex(currentlyAdded, r => r.rowId === rowId)
    currentlyAdded.splice(idx, 1)
    setAddedStations({
      ...addedStations,
      [planningAreaId]: currentlyAdded
    })
  }

  /** Edits net new stations */
  const handleEditStation = (planningAreaId: number, rowId: number, row: StationAdminRow) => {
    const currentlyAdded = addedStations[planningAreaId]
    const idx = findIndex(currentlyAdded, r => r.rowId === rowId)
    currentlyAdded.splice(idx, 1, row)
    setAddedStations({
      ...addedStations,
      [planningAreaId]: currentlyAdded
    })
  }

  /** Removes existing stations, not net new ones */
  const handleRemoveExistingStation = (planningAreaId: number, rowId: number, station: BasicWFWXStation) => {
    const currentRow = removedStations[planningAreaId].concat({ planningAreaId, rowId, station })
    setRemovedStations({
      ...removedStations,
      [planningAreaId]: currentRow
    })
  }

  const handleSave = () => {
    const allAdded = Object.values(addedStations).flat()
    const allRemoved = Object.values(removedStations).flat()
    if (every(allAdded, addedStation => !isUndefined(addedStation.station) && !isUndefined(addedStation.fuelType))) {
      dispatch(
        fetchAddOrUpdateStations(
          fireCentreId,
          allAdded as Required<StationAdminRow>[],
          allRemoved as Required<StationAdminRow>[]
        )
      )
      handleClose()
    }
  }

  return (
    <Box sx={{ width: '100%', pl: 4 }} aria-labelledby="planning-areas-admin">
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
