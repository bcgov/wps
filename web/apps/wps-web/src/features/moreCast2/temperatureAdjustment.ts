import { ModelChoice } from '@wps/api/moreCast2API'
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
  const changed: MoreCast2Row[] = []
  let occupied = 0
  let unavailable = 0
  for (const row of getForecastRows(rows)) {
    if (row.stationCode !== stationCode) continue
    if (!overwriteExisting && row.tempForecast && !Number.isNaN(row.tempForecast.value)) {
      occupied++
      continue
    }
    const temperature = row[`temp${model}` as keyof MoreCast2Row]
    if (typeof temperature !== 'number' || !Number.isFinite(temperature)) {
      unavailable++
      continue
    }
    const value = temperature + adjustment
    if (!Number.isFinite(value) || value < -60 || value > 60) {
      return { rows: [], message: 'Adjusted temperatures must be between -60°C and 60°C. No forecasts were changed.' }
    }
    changed.push({ ...row, tempForecast: { choice: ModelChoice.MANUAL, value } })
  }
  return {
    rows: changed,
    message: [
      `${overwriteExisting ? 'Replaced' : 'Filled'} temperature forecasts for ${changed.length} days.`,
      occupied ? `Skipped ${occupied} days with existing forecasts.` : '',
      unavailable ? `Model temperatures unavailable for ${unavailable} days.` : ''
    ]
      .filter(Boolean)
      .join(' ')
  }
}
