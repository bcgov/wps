import React, { useState } from 'react'
import { FuelType, PlanningArea } from 'api/hfiCalculatorAPI'
import { sortBy, maxBy, findIndex, every, isUndefined } from 'lodash'
import PlanningAreaAdmin from 'features/hfiCalculator/components/stationAdmin/PlanningAreaAdmin'
import { Box } from '@mui/material'
import { AddStationOptions, StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import SaveNewStationButton from 'features/hfiCalculator/components/stationAdmin/SaveNewStationButton'
import AdminCancelButton from 'features/hfiCalculator/components/stationAdmin/AdminCancelButton'
import { fetchAddOrUpdateStations } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { AppDispatch } from 'app/store'
import { useDispatch } from 'react-redux'

export interface AdminHandlers {
  handleRemoveExistingStation: (planningAreaId: number, rowId: number) => void
  handleAddStation: (planningAreaId: number) => void
  handleRemoveStation: (planningAreaId: number, rowId: number) => void
}

export interface StationListAdminProps {
  fireCentreId: number
  planningAreas: PlanningArea[]
  fuelTypes: Pick<FuelType, 'id' | 'abbrev'>[]
  addStationOptions?: AddStationOptions
  existingPlanningAreaStations: { [key: string]: StationAdminRow[] }
  handleCancel: () => void
}

const StationListAdmin = ({
  fireCentreId,
  planningAreas,
  addStationOptions,
  existingPlanningAreaStations,
  handleCancel
}: StationListAdminProps) => {
  const dispatch: AppDispatch = useDispatch()

  const [addedStations, setAddedStations] = useState<{ [key: string]: StationAdminRow[] }>(
    Object.keys(existingPlanningAreaStations).reduce((accumulator, key) => {
      return { ...accumulator, [key]: [] }
    }, {})
  )
  const [removedStations, setRemovedStations] = useState<{
    [key: string]: { planningAreaId: number; rowId: number }[]
  }>(
    Object.keys(existingPlanningAreaStations).reduce((accumulator, key) => {
      return { ...accumulator, [key]: [] }
    }, {})
  )

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

  /** Removes existing stations, not net new ones */
  const handleRemoveExistingStation = (planningAreaId: number, rowId: number) => {
    const currentRow = removedStations[planningAreaId].concat({ planningAreaId, rowId })
    setRemovedStations({
      ...removedStations,
      [planningAreaId]: currentRow
    })
  }

  const handleSave = () => {
    /** TODO */
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
    }
  }

  return (
    <Box sx={{ width: '100%', pl: 4 }} aria-labelledby="planning-areas-admin">
      {sortBy(planningAreas, planningArea => planningArea.order_of_appearance_in_list).map((area, index) => (
        <PlanningAreaAdmin
          key={`planning-area-admin-${index}`}
          planningArea={area}
          existingStations={existingPlanningAreaStations}
          addedStations={addedStations}
          removedStations={removedStations}
          addStationOptions={addStationOptions}
          adminHandlers={{
            handleAddStation,
            handleRemoveStation,
            handleRemoveExistingStation
          }}
        />
      ))}
      <SaveNewStationButton handleSave={handleSave} />
      <AdminCancelButton handleCancel={handleCancel} />
    </Box>
  )
}

export default React.memo(StationListAdmin)
