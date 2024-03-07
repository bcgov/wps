import React from 'react'
import { Button } from '@mui/material'
import { fillGrassCuringForecast } from 'features/moreCast2/util'
import { MoreCast2Row, PredictionItem } from 'features/moreCast2/interfaces'
import { ModelChoice, WeatherDeterminate } from 'api/moreCast2API'
import { MorecastDraftForecast } from 'features/moreCast2/forecastDraft'

export interface ResetForecastButtonProps {
  className?: string
  enabled: boolean
  label: string
  allRows: MoreCast2Row[]
  setAllRows: React.Dispatch<React.SetStateAction<MoreCast2Row[]>>
}

const ResetForecastButton = ({ className, enabled, label, allRows, setAllRows }: ResetForecastButtonProps) => {
  /**
   * Reset forecast rows to their default state. Temp, RH, Wind Dir & Speed are cleared,
   * Precip is set to 0, and GC is carried forward from last submitted value.
   */
  const resetForecastRows = () => {
    const resetRows = allRows.map(row => {
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
    setAllRows(resetRows)
    fillGrassCuringForecast(allRows)
  }

  const storedDraftForecast = new MorecastDraftForecast(localStorage)

  const handleResetClick = () => {
    resetForecastRows()
    storedDraftForecast.clearDraftForecasts()
  }

  return (
    <Button
      className={className}
      variant="contained"
      data-testid={'reset-forecast-button'}
      disabled={!enabled}
      onClick={handleResetClick}
    >
      {label}
    </Button>
  )
}

export default React.memo(ResetForecastButton)
