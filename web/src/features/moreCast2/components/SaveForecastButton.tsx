import React from 'react'
import SaveIcon from '@mui/icons-material/Save'
import { Button } from '@mui/material'
import { ForecastActionChoice, ForecastActionType } from 'api/moreCast2API'

export interface SubmitForecastButtonProps {
  enabled: boolean
  mode: ForecastActionType
  onClick: () => void
}

const SaveForecastButton = ({ enabled, mode, onClick }: SubmitForecastButtonProps) => {
  const buttonText = mode === ForecastActionChoice.CREATE ? 'Save Forecast' : 'Update Forecast'
  return (
    <Button
      variant="contained"
      data-testid={'submit-forecast-button'}
      disabled={!enabled}
      onClick={onClick}
      startIcon={<SaveIcon />}
    >
      {buttonText}
    </Button>
  )
}

export default React.memo(SaveForecastButton)
