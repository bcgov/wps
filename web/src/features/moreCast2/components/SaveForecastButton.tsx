import React from 'react'
import SaveIcon from '@mui/icons-material/Save'
import { Button } from '@mui/material'

export interface SubmitForecastButtonProps {
  enabled: boolean
}

const SaveForecastButton = ({ enabled }: SubmitForecastButtonProps) => {
  return (
    <Button variant="contained" data-testid={'submit-forecast-button'} disabled={!enabled} startIcon={<SaveIcon />}>
      Save Forecast
    </Button>
  )
}

export default React.memo(SaveForecastButton)
