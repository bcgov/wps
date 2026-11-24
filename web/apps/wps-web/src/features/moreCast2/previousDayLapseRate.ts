import type { WeatherIndeterminatePayload } from '@wps/api/moreCast2API'
import { isNumber } from 'lodash'
import { DateTime } from 'luxon'

export type PreviousDayWeather = Pick<WeatherIndeterminatePayload, 'actuals' | 'predictions'>

export interface LapseRateEstimate {
  rate: number | null
  explanation: string
}

const MINIMUM_ELEVATION_DIFFERENCE_METRES = 100
const MAXIMUM_AUTOMATIC_LAPSE_RATE = 9.8

const finite = (value: unknown): value is number => isNumber(value) && Number.isFinite(value)

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

  const observedTemperature = actual?.temperature
  const modelTemperature = prediction?.temperature
  const modelElevation = prediction?.model_elevation

  if (!finite(observedTemperature) || !finite(modelTemperature)) {
    return { rate: null, explanation: "Yesterday's matching observed or raw model temperature is unavailable." }
  }
  if (!finite(modelElevation) || !finite(stationElevation)) {
    return { rate: null, explanation: "The station elevation or yesterday's model elevation is unavailable." }
  }

  const elevationDifferenceMetres = modelElevation - stationElevation
  if (Math.abs(elevationDifferenceMetres) < MINIMUM_ELEVATION_DIFFERENCE_METRES) {
    return { rate: null, explanation: 'The elevation difference is less than 100 m, so no lapse rate is prefilled.' }
  }

  const estimatedRate = (observedTemperature - modelTemperature) / (elevationDifferenceMetres / 1000)
  if (!Number.isFinite(estimatedRate))
    return { rate: null, explanation: 'A finite lapse rate could not be calculated.' }

  // limit automatic estimates while leaving manual input unrestricted
  const rate = Number(
    Math.max(-MAXIMUM_AUTOMATIC_LAPSE_RATE, Math.min(MAXIMUM_AUTOMATIC_LAPSE_RATE, estimatedRate)).toFixed(1)
  )

  return {
    rate,
    explanation: `${date.toISODate()} at 20:00 UTC. Observed: ${observedTemperature}°C; raw ${model}: ${modelTemperature}°C. Station elevation: ${stationElevation} m; model elevation: ${modelElevation} m. Estimated rate: ${rate.toFixed(1)}°C/km. Model run: ${prediction?.prediction_run_timestamp ?? 'unavailable'}.`
  }
}
