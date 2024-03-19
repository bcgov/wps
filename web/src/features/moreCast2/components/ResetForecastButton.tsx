import React from 'react'
import { Button } from '@mui/material'

export interface ResetForecastButtonProps {
  className?: string
  enabled: boolean
  label: string
  onClick: () => void
}

const ResetForecastButton = ({ className, enabled, label, onClick }: ResetForecastButtonProps) => {
  return (
    <Button
      className={className}
      variant="contained"
      data-testid={'reset-forecast-button'}
      disabled={!enabled}
      onClick={onClick}
    >
      {label}
    </Button>
  )
}

export default React.memo(ResetForecastButton)
