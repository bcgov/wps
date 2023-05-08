import React from 'react'
import SaveIcon from '@mui/icons-material/Save'
import { Button } from '@mui/material'

export interface SubmitForecastButtonProps {
  className?: string
  enabled: boolean
  label: string
  onClick: () => void
}

const SaveForecastButton = ({ className, enabled, label, onClick }: SubmitForecastButtonProps) => {
  return (
    <Button
      className={className}
      variant="contained"
      data-testid={'submit-forecast-button'}
      disabled={!enabled}
      onClick={onClick}
      startIcon={<SaveIcon />}
    >
      {label}
    </Button>
  )
}

export default React.memo(SaveForecastButton)
