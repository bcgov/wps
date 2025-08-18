import axios from 'api/axios'
import { isEqual } from 'lodash'
import { DateTime } from 'luxon'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'

export enum ModelChoice {
  ACTUAL = 'ACTUAL',
  FORECAST = 'FORECAST',
  GDPS = 'GDPS',
  GDPS_BIAS = 'GDPS_BIAS',
  GFS = 'GFS',
  GFS_BIAS = 'GFS_BIAS',
  HRDPS = 'HRDPS',
  HRDPS_BIAS = 'HRDPS_BIAS',
  MANUAL = 'MANUAL',
  NAM = 'NAM',
  NAM_BIAS = 'NAM_BIAS',
  NULL = 'NULL',
  PERSISTENCE = 'PERSISTENCE',
  RDPS = 'RDPS',
  RDPS_BIAS = 'RDPS_BIAS'
}

export const DEFAULT_MODEL_TYPE: ModelType = ModelChoice.HRDPS

export type ModelType =
  | ''
  | 'ACTUAL'
  | 'FORECAST'
  | 'GDPS'
  | 'GDPS_BIAS'
  | 'GFS'
  | 'GFS_BIAS'
  | 'HRDPS'
  | 'HRDPS_BIAS'
  | 'MANUAL'
  | 'NAM'
  | 'NAM_BIAS'
  | 'NULL'
  | 'PERSISTENCE'
  | 'RDPS'
  | 'RDPS_BIAS'
  | 'Grass_Curing_CWFIS'

export const ModelChoices: ModelType[] = [
  ModelChoice.GDPS,
  ModelChoice.GDPS_BIAS,
  ModelChoice.GFS,
  ModelChoice.GFS_BIAS,
  ModelChoice.HRDPS,
  ModelChoice.HRDPS_BIAS,
  ModelChoice.PERSISTENCE,
  ModelChoice.MANUAL,
  ModelChoice.NAM,
  ModelChoice.NAM_BIAS,
  ModelChoice.NULL,
  ModelChoice.RDPS,
  ModelChoice.RDPS_BIAS
]

export const WeatherModelChoices: ModelType[] = [
  ModelChoice.GDPS,
  ModelChoice.GDPS_BIAS,
  ModelChoice.GFS,
  ModelChoice.GFS_BIAS,
  ModelChoice.HRDPS,
  ModelChoice.HRDPS_BIAS,
  ModelChoice.NAM,
  ModelChoice.NAM_BIAS,
  ModelChoice.RDPS,
  ModelChoice.RDPS_BIAS
]

export enum WeatherDeterminate {
  ACTUAL = 'Actual',
  FORECAST = 'Forecast',
  GDPS = 'GDPS',
  GDPS_BIAS = 'GDPS_BIAS',
  GFS = 'GFS',
  GFS_BIAS = 'GFS_BIAS',
  HRDPS = 'HRDPS',
  HRDPS_BIAS = 'HRDPS_BIAS',
  NAM = 'NAM',
  NAM_BIAS = 'NAM_BIAS',
  NULL = 'NULL',
  RDPS = 'RDPS',
  RDPS_BIAS = 'RDPS_BIAS',
  GRASS_CURING_CWFIS = 'Grass_Curing_CWFIS',
  GC = 'GC'
}

export type WeatherDeterminateType =
  | 'Actual'
  | 'Forecast'
  | 'GDPS'
  | 'GDPS_BIAS'
  | 'GFS'
  | 'GFS_BIAS'
  | 'HRDPS'
  | 'HRDPS_BIAS'
  | 'NAM'
  | 'NAM_BIAS'
  | 'NULL'
  | 'RDPS'
  | 'RDPS_BIAS'
  | 'Grass_Curing_CWFIS'
  | 'GC'

export const WeatherDeterminateChoices = [
  WeatherDeterminate.ACTUAL,
  WeatherDeterminate.FORECAST,
  WeatherDeterminate.GDPS,
  WeatherDeterminate.GDPS_BIAS,
  WeatherDeterminate.GFS,
  WeatherDeterminate.GFS_BIAS,
  WeatherDeterminate.HRDPS,
  WeatherDeterminate.HRDPS_BIAS,
  WeatherDeterminate.NAM,
  WeatherDeterminate.NAM_BIAS,
  WeatherDeterminate.NULL,
  WeatherDeterminate.RDPS,
  WeatherDeterminate.RDPS_BIAS
]

export const weatherModelsWithTooltips = [
  WeatherDeterminate.HRDPS,
  WeatherDeterminate.RDPS,
  WeatherDeterminate.GDPS,
  WeatherDeterminate.NAM,
  WeatherDeterminate.GFS
]

export interface WeatherIndeterminate {
  id: string
  station_code: number
  station_name: string
  latitude: number
  longitude: number
  determinate: WeatherDeterminateType
  utc_timestamp: string
  precipitation: number | null
  relative_humidity: number | null
  temperature: number | null
  wind_direction: number | null
  wind_speed: number | null
  fine_fuel_moisture_code: number | null
  duff_moisture_code: number | null
  drought_code: number | null
  initial_spread_index: number | null
  build_up_index: number | null
  fire_weather_index: number | null
  danger_rating: number | null
  grass_curing: number | null
  prediction_run_timestamp: string | null
}

export interface WeatherIndeterminatePayload {
  actuals: WeatherIndeterminate[]
  forecasts: WeatherIndeterminate[]
  grassCuring: WeatherIndeterminate[]
  predictions: WeatherIndeterminate[]
}

export interface WeatherIndeterminateResponse {
  actuals: WeatherIndeterminate[]
  forecasts: WeatherIndeterminate[]
  grass_curing: WeatherIndeterminate[]
  predictions: WeatherIndeterminate[]
}

export const ModelOptions: ModelType[] = ModelChoices.filter(choice => !isEqual(choice, ModelChoice.MANUAL))

export interface MoreCast2ForecastRecord {
  station_code: number
  for_date: number
  temp: number
  rh: number
  precip: number
  wind_speed: number
  wind_direction: number
  update_timestamp?: number
  station_name?: string
  grass_curing: number
}

export interface MoreCastForecastRequest {
  forecasts: MoreCast2ForecastRecord[]
}

export const marshalMoreCast2ForecastRecords = (forecasts: MoreCast2ForecastRow[]): MoreCast2ForecastRecord[] => {
  const forecastRecords: MoreCast2ForecastRecord[] = forecasts.map(forecast => {
    return {
      station_code: forecast.stationCode,
      for_date: forecast.forDate.toMillis(),
      precip: forecast.precip.value,
      rh: forecast.rh.value,
      temp: Math.round(forecast.temp.value),
      wind_direction: Math.round(forecast.windDirection.value),
      wind_speed: Math.round(forecast.windSpeed.value),
      grass_curing: forecast.grassCuring.value
    }
  })
  return forecastRecords
}

/**
 * POSTs a batch of forecasts.
 * @param token The WF1 token.
 * @param forecasts The raw forecast model data.
 * @returns True if the response is a 201, otherwise false.
 */
export async function submitMoreCastForecastRecords(
  forecasts: MoreCast2ForecastRow[]
): Promise<{ success: boolean; errorMessage?: string }> {
  const forecastRecords = marshalMoreCast2ForecastRecords(forecasts)
  const url = `/morecast-v2/forecast`
  try {
    const { status } = await axios.post<MoreCastForecastRequest>(url, {
      forecasts: forecastRecords
    })
    return { success: status === 201 }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (error: any) {
    console.error(error.response.data.detail || error)
    return { success: false, errorMessage: error.response.data.detail }
  }
}

export async function fetchWeatherIndeterminates(
  stationCodes: number[],
  startDate: DateTime,
  endDate: DateTime
): Promise<WeatherIndeterminatePayload> {
  if (stationCodes.length === 0) {
    return {
      actuals: [],
      forecasts: [],
      grassCuring: [],
      predictions: []
    }
  }
  const url = `/morecast-v2/determinates/${startDate.toISODate()}/${endDate.toISODate()}`
  const { data } = await axios.post<WeatherIndeterminateResponse>(url, {
    stations: stationCodes
  })
  const payload: WeatherIndeterminatePayload = {
    actuals: data.actuals,
    forecasts: data.forecasts,
    grassCuring: data.grass_curing,
    predictions: data.predictions
  }

  return payload
}
