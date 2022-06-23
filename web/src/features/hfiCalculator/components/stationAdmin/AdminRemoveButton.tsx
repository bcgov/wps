import React from 'react'
import { isUndefined } from 'lodash'
import { IconButton } from '@mui/material'
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined'
import { StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'

export interface AdminRemoveButtonProps {
  adminRow: StationAdminRow
  planningAreaId: number
  handleRemoveStation: (planningAreaId: number, rowId: number) => void
}

const AdminRemoveButton = ({ adminRow, planningAreaId, handleRemoveStation }: AdminRemoveButtonProps) => {
  return (
    <IconButton
      data-testid={'admin-remove-button'}
      color="primary"
      size="large"
      onClick={() => {
        if (!isUndefined(adminRow)) {
          handleRemoveStation(planningAreaId, adminRow.rowId)
        }
      }}
    >
      <DeleteOutlinedIcon />
    </IconButton>
  )
}

export default React.memo(AdminRemoveButton)
