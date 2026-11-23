import type { WeatherIndeterminatePayload } from '@wps/api/moreCast2API'
import { DateTime } from 'luxon'

export type PreviousDayWeather = Pick<WeatherIndeterminatePayload, 'actuals' | 'predictions'>

export interface LapseRateEstimate {
  rate: number | null
  explanation: string
}

const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)

export const estimatePreviousDayLapseRate = (
  data: PreviousDayWeather,
  stationCode: number,
  stationElevation: number | null,
  model: string,
  date: DateTime
): LapseRateEstimate => {
  const timestamp = DateTime.fromISO(`${date.toISODate()}T20:00:00Z`).toMillis()
  const prediction = data.predictions.find(
    row => row.station_code === stationCode && row.determinate === model && Date.parse(row.utc_timestamp) === timestamp
  )
  const actual = data.actuals.find(
    row => row.station_code === stationCode && Date.parse(row.utc_timestamp) === timestamp
  )
  const observed = actual?.temperature
  const predicted = prediction?.temperature
  const elevation = prediction?.model_elevation
  if (!finite(observed) || !finite(predicted)) {
    return { rate: null, explanation: "Yesterday's matching observed or raw model temperature is unavailable." }
  }
  if (!finite(elevation) || !finite(stationElevation)) {
    return { rate: null, explanation: "The station elevation or yesterday's model elevation is unavailable." }
  }
  if (elevation === stationElevation) {
    return { rate: null, explanation: 'Station and model elevations are equal, so a lapse rate cannot be calculated.' }
  }
  const rate = Number(((observed - predicted) / ((elevation - stationElevation) / 1000)).toFixed(1))
  if (!Number.isFinite(rate)) return { rate: null, explanation: 'A finite lapse rate could not be calculated.' }
  return {
    rate,
    explanation: `${date.toISODate()} at 20:00 UTC. Observed: ${observed}°C; raw ${model}: ${predicted}°C. Station elevation: ${stationElevation} m; model elevation: ${elevation} m. Estimated rate: ${rate.toFixed(1)}°C/km. Model run: ${prediction?.prediction_run_timestamp ?? 'unavailable'}.`
  }
}
