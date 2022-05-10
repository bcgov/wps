import { ToggleButton } from '@mui/material'
import ToggleOffOutlinedIcon from '@mui/icons-material/ToggleOffOutlined'
import ToggleOnOutlinedIcon from '@mui/icons-material/ToggleOnOutlined'
import React from 'react'

export interface PlanningAreaReadyToggleProps {
  disabled: boolean
}

const PlanningAreaReadyToggle = ({ disabled }: PlanningAreaReadyToggleProps) => {
  const [ready, setReady] = React.useState(false)

  return (
    <ToggleButton
      disabled={disabled}
      value="ready"
      selected={ready}
      onChange={() => {
        setReady(!ready)
      }}
    >
      {ready ? <ToggleOnOutlinedIcon color="success" /> : <ToggleOffOutlinedIcon />}
    </ToggleButton>
  )
}

export default React.memo(PlanningAreaReadyToggle)
