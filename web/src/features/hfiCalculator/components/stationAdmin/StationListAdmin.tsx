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
  handleEditStation: (planningAreaId: number, rowId: number, row: StationAdminRow) => void
  handleRemoveStation: (planningAreaId: number, rowId: number) => void
  handleAddStation: (planningAreaId: number) => void
}

export interface StationListAdminProps {
  fireCentreId: number
  planningAreas: PlanningArea[]
  fuelTypes: Pick<FuelType, 'id' | 'abbrev'>[]
  addStationOptions?: AddStationOptions
  adminRows: { [key: string]: StationAdminRow[] }
  handleCancel: () => void
}

const StationListAdmin = ({
  fireCentreId,
  planningAreas,
  addStationOptions,
  adminRows,
  handleCancel
}: StationListAdminProps) => {
  const dispatch: AppDispatch = useDispatch()

  const [adminRowList, setAdminRows] = useState<{ [key: string]: StationAdminRow[] }>(adminRows)

  const handleAddStation = (planningAreaId: number) => {
    const lastRowId = maxBy(adminRows[planningAreaId], 'rowId')?.rowId
    if (lastRowId) {
      const currentRow = adminRowList[planningAreaId].concat([{ planningAreaId, rowId: lastRowId + 1 }])
      setAdminRows({
        ...adminRowList,
        [planningAreaId]: currentRow
      })
    }
  }

  const handleEditStation = (planningAreaId: number, rowId: number, row: StationAdminRow) => {
    const currentRow = adminRowList[planningAreaId]
    const idx = findIndex(currentRow, r => r.rowId === rowId)
    currentRow.splice(idx, 1, row)
    setAdminRows({
      ...adminRowList,
      [planningAreaId]: currentRow
    })
  }

  const handleRemoveStation = (planningAreaId: number, rowId: number) => {
    const currentRow = adminRowList[planningAreaId]
    const idx = findIndex(currentRow, row => row.rowId === rowId)
    currentRow.splice(idx, 1)

    setAdminRows({
      ...adminRowList,
      [planningAreaId]: currentRow
    })
  }

  const handleSave = () => {
    const commands = Object.values(adminRowList)
      .flat()
      .filter(station => !isUndefined(station.command))
    if (every(commands, addedStation => !isUndefined(addedStation.station) && !isUndefined(addedStation.fuelType))) {
      dispatch(fetchAddOrUpdateStations(fireCentreId, commands as Required<StationAdminRow>[]))
    }
  }

  return (
    <Box sx={{ width: '100%', pl: 4 }} aria-labelledby="planning-areas-admin">
      {sortBy(planningAreas, planningArea => planningArea.order_of_appearance_in_list).map((area, index) => (
        <PlanningAreaAdmin
          key={`planning-area-admin-${index}`}
          planningArea={area}
          planningAreaAdminStations={adminRowList}
          addStationOptions={addStationOptions}
          adminHandlers={{
            handleAddStation,
            handleEditStation,
            handleRemoveStation
          }}
        />
      ))}
      <SaveNewStationButton handleSave={handleSave} />
      <AdminCancelButton handleCancel={handleCancel} />
    </Box>
  )
}

export default React.memo(StationListAdmin)
