import { ModelChoice } from '@wps/api/moreCast2API'
import { isNumber } from 'lodash'
import type { MoreCast2Row } from './interfaces'
import { getForecastRows } from './saveForecasts'

// calculate from model values so applying twice never compounds the adjustment
export const adjustStationTemperatures = (
  rows: MoreCast2Row[],
  stationCode: number,
  model: string,
  adjustment: number,
  overwriteExisting = false
): { rows: MoreCast2Row[]; message: string } => {
  if (!Number.isFinite(adjustment)) {
    return { rows: [], message: 'A valid temperature adjustment is required.' }
  }

  const updatedRows: MoreCast2Row[] = []
  let existingForecastCount = 0
  let unavailableModelCount = 0

  for (const row of getForecastRows(rows)) {
    if (row.stationCode !== stationCode) continue
    if (!overwriteExisting && row.tempForecast && !Number.isNaN(row.tempForecast.value)) {
      existingForecastCount++
      continue
    }

    const temperature = row[`temp${model}` as keyof MoreCast2Row]
    if (!isNumber(temperature) || !Number.isFinite(temperature)) {
      unavailableModelCount++
      continue
    }

    const value = temperature + adjustment
    if (!Number.isFinite(value) || value < -60 || value > 60) {
      // reject the batch so an invalid day does not leave a partially filled forecast
      return { rows: [], message: 'Adjusted temperatures must be between -60°C and 60°C. No forecasts were changed.' }
    }

    updatedRows.push({ ...row, tempForecast: { choice: ModelChoice.MANUAL, value } })
  }

  return {
    rows: updatedRows,
    message: [
      `${overwriteExisting ? 'Replaced' : 'Filled'} temperature forecasts for ${updatedRows.length} days.`,
      existingForecastCount ? `Skipped ${existingForecastCount} days with existing forecasts.` : '',
      unavailableModelCount ? `Model temperatures unavailable for ${unavailableModelCount} days.` : ''
    ]
      .filter(Boolean)
      .join(' ')
  }
}
