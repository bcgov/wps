import React from 'react'
import SaveIcon from '@mui/icons-material/Save'
import { Button } from '@mui/material'

export interface SubmitForecastButtonProps {
  onClick: () => void
  enabled: boolean
}

const SaveForecastButton = ({ enabled, onClick }: SubmitForecastButtonProps) => {
  return (
    <Button
      variant="contained"
      data-testid={'submit-forecast-button'}
      disabled={!enabled}
      onClick={onClick}
      startIcon={<SaveIcon />}
    >
      Save Forecast
    </Button>
  )
}

export default React.memo(SaveForecastButton)
