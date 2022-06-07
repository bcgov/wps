import { IconButton } from '@mui/material'
import ToggleOffOutlinedIcon from '@mui/icons-material/ToggleOffOutlined'
import ToggleOnOutlinedIcon from '@mui/icons-material/ToggleOnOutlined'
import React from 'react'
import { ReadyPlanningAreaDetails } from 'api/hfiCalculatorAPI'
import { isUndefined } from 'lodash'

export interface PlanningAreaReadyToggleProps {
  disabled: boolean
  loading: boolean
  readyDetails?: ReadyPlanningAreaDetails
  toggleReady: (planningAreaId: number, hfiRequestId: number) => void
}

const PlanningAreaReadyToggle = ({ disabled, loading, readyDetails, toggleReady }: PlanningAreaReadyToggleProps) => {
  return (
    <IconButton
      aria-label="hfi-toggle-ready"
      data-testid="hfi-toggle-ready"
      disabled={disabled || loading}
      onClick={() => {
        if (!isUndefined(readyDetails)) {
          toggleReady(readyDetails.planning_area_id, readyDetails.hfi_request_id)
        }
      }}
    >
      {readyDetails?.ready ? (
        <ToggleOnOutlinedIcon fontSize="large" color="success" />
      ) : (
        <ToggleOffOutlinedIcon fontSize="large" />
      )}
    </IconButton>
  )
}

export default React.memo(PlanningAreaReadyToggle)
