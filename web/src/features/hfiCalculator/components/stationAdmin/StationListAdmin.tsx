import React, { useState } from 'react'
import { FuelType, PlanningArea } from 'api/hfiCalculatorAPI'
import { sortBy } from 'lodash'
import PlanningAreaAdmin from 'features/hfiCalculator/components/stationAdmin/PlanningAreaAdmin'
import { Box } from '@mui/material'
import { maxBy, findIndex } from 'lodash'
import { AddStationOptions, StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'

export interface AdminHandlers {
  handleEditStation: (planningAreaId: number, rowId: number, row: StationAdminRow) => void
  handleRemoveStation: (planningAreaId: number, rowId: number) => void
  handleAddStation: (planningAreaId: number) => void
}

export interface StationListAdminProps {
  planningAreas: PlanningArea[]
  fuelTypes: FuelType[]
  addStationOptions?: AddStationOptions
  adminRows: { [key: string]: StationAdminRow[] }
}

const StationListAdmin = ({ planningAreas, addStationOptions, adminRows }: StationListAdminProps) => {
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
    const idx = findIndex(currentRow, row => row.rowId === rowId)
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

  return (
    <Box sx={{ width: '100%', pl: 4 }} aria-labelledby="planning-areas-admin">
      {sortBy(planningAreas, planningArea => planningArea.order_of_appearance_in_list).map((area, index) => (
        <PlanningAreaAdmin
          key={`planning-area-admin-${index}`}
          planningArea={area}
          adminRows={adminRowList}
          addStationOptions={addStationOptions}
          adminHandlers={{
            handleAddStation,
            handleEditStation,
            handleRemoveStation
          }}
        />
      ))}
    </Box>
  )
}

export default React.memo(StationListAdmin)
