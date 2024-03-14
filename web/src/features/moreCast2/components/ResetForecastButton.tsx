import React from 'react'
import { Button } from '@mui/material'
import { fillGrassCuringForecast } from 'features/moreCast2/util'
import { MoreCast2Row, PredictionItem } from 'features/moreCast2/interfaces'
import { ModelChoice, WeatherDeterminate } from 'api/moreCast2API'

export interface ResetForecastButtonProps {
  className?: string
  enabled: boolean
  label: string
  onClick: () => void
}

/**
 * Reset forecast rows to their default state. Temp, RH, Wind Dir & Speed are cleared,
 * Precip is set to 0, and GC is carried forward from last submitted value.
 */
export const resetForecastRows = (rows: MoreCast2Row[]) => {
  const resetRows = rows.map(row => {
    const rowToReset = { ...row }
    Object.keys(rowToReset).forEach(key => {
      if (key.includes(WeatherDeterminate.FORECAST)) {
        const isPrecipField = key.includes('precip')
        const field = rowToReset[key as keyof MoreCast2Row] as PredictionItem
        // Submitted forecasts have a ModelChoice.FORECAST, we don't want to reset those
        if (field.choice != ModelChoice.FORECAST && !isNaN(field.value)) {
          field.value = isPrecipField ? 0 : NaN
          field.choice = ''
        }
      }
    })
    return rowToReset
  })
  fillGrassCuringForecast(resetRows)
  return resetRows
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
