import { IconButton } from '@mui/material'
import ToggleOffOutlinedIcon from '@mui/icons-material/ToggleOffOutlined'
import ToggleOnOutlinedIcon from '@mui/icons-material/ToggleOnOutlined'
import React from 'react'

export interface PlanningAreaReadyToggleProps {
  disabled: boolean
}

const PlanningAreaReadyToggle = ({ disabled }: PlanningAreaReadyToggleProps) => {
  const [ready, setReady] = React.useState(false)

  return (
    <IconButton
      aria-label="hfi-toggle-ready"
      data-testid="hfi-toggle-ready"
      disabled={disabled}
      onClick={() => {
        setReady(!ready)
      }}
    >
      {ready ? (
        <ToggleOnOutlinedIcon fontSize="large" color="success" />
      ) : (
        <ToggleOffOutlinedIcon fontSize="large" />
      )}
    </IconButton>
  )
}

export default React.memo(PlanningAreaReadyToggle)
