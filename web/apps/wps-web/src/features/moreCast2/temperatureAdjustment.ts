import { ModelChoice } from '@wps/api/moreCast2API'
import type { MoreCast2Row } from './interfaces'
import type { ModelElevationRow } from './modelElevation'
import { getForecastRows } from './saveForecasts'

// calculate from model values so applying twice never compounds the adjustment
export const adjustStationTemperatures = (
  rows: MoreCast2Row[],
  stationCode: number,
  model: string,
  rate: number,
  elevations: Pick<ModelElevationRow, 'stationElevation' | 'modelElevations'> | undefined
): { rows: MoreCast2Row[]; message: string } => {
  const stationElevation = elevations?.stationElevation
  const modelElevation = elevations?.modelElevations[model as keyof NonNullable<typeof elevations>['modelElevations']]
  if (
    typeof stationElevation !== 'number' ||
    !Number.isFinite(stationElevation) ||
    typeof modelElevation !== 'number' ||
    !Number.isFinite(modelElevation) ||
    !Number.isFinite(rate)
  ) {
    return { rows: [], message: 'A valid rate and station and model elevations are required.' }
  }
  const adjustment = (rate * (modelElevation - stationElevation)) / 1000
  const changed: MoreCast2Row[] = []
  for (const row of getForecastRows(rows)) {
    if (row.stationCode !== stationCode) continue
    const temperature = row[`temp${model}` as keyof MoreCast2Row]
    if (typeof temperature !== 'number' || !Number.isFinite(temperature)) continue
    const value = temperature + adjustment
    if (!Number.isFinite(value) || value < -60 || value > 60) {
      return { rows: [], message: 'Adjusted temperatures must be between -60°C and 60°C. No forecasts were changed.' }
    }
    changed.push({ ...row, tempForecast: { choice: ModelChoice.MANUAL, value } })
  }
  return {
    rows: changed,
    message: changed.length
      ? `Updated temperature forecasts for ${changed.length} days.`
      : 'No eligible days have model temperatures.'
  }
}
