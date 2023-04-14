import axios from 'api/axios'
import { Station } from 'api/stationAPI'
import { rowIDHasher } from 'features/moreCast2/util'
import { isEqual } from 'lodash'
import { DateTime } from 'luxon'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'

export enum ModelChoice {
  FORECAST = 'FORECAST',
  GDPS = 'GDPS',
  GFS = 'GFS',
  HRDPS = 'HRDPS',
  NAM = 'NAM',
  RDPS = 'RDPS',
  MANUAL = 'MANUAL',
  YESTERDAY = 'YESTERDAY',
  ACTUAL = 'ACTUAL'
}

export const DEFAULT_MODEL_TYPE: ModelType = ModelChoice.HRDPS

export type ModelType = 'HRDPS' | 'GDPS' | 'GFS' | 'YESTERDAY' | 'NAM' | 'RDPS' | 'MANUAL' | 'FORECAST' | 'ACTUAL'

export const ModelChoices: ModelType[] = [
  ModelChoice.GDPS,
  ModelChoice.GFS,
  ModelChoice.HRDPS,
  ModelChoice.YESTERDAY,
  ModelChoice.MANUAL,
  ModelChoice.NAM,
  ModelChoice.RDPS
]

export enum WeatherDeterminate {
  GDPS = 'GDPS',
  GFS = 'GFS',
  HRDPS = 'HRDPS',
  RDPS = 'RDPS',
  ACTUAL = 'ACTUAL'
}

export type WeatherDeterminateType = 'ACTUAL' | 'GDPS' | 'GFS' | 'HRDPS' | 'RDPS'

export const WeatherDeterminateChoices: WeatherDeterminateType[] = [
  WeatherDeterminate.ACTUAL,
  WeatherDeterminate.GDPS,
  WeatherDeterminate.GFS,
  WeatherDeterminate.HRDPS,
  WeatherDeterminate.RDPS
]

export interface StationWeatherIndeterminate {
  id: string
  station_code: number
  station_name: string
  determinate: WeatherDeterminateType
  utc_timestamp: string
  precipitation: number | null
  relative_humidity: number | null
  temperature: number | null
  wind_direction: number | null
  wind_speed: number | null
}

export interface StationWeatherIndeterminateResponse {
  actuals: StationWeatherIndeterminate[]
  forecasts: StationWeatherIndeterminate[]
  predictions: StationWeatherIndeterminate[]
}

export interface ObservedDailiesResponse {
  dailies: ObservedDailyResponse[]
}

export interface ObservedDailyResponse {
  station_code: number
  station_name: string
  utcTimestamp: string
  temperature: number | null
  relative_humidity: number | null
  precipitation: number | null
  wind_direction: number | null
  wind_speed: number | null
}

export interface ObservedDaily extends ObservedDailyResponse {
  id: string
  data_type: 'ACTUAL' | 'YESTERDAY'
}

export interface ObservedAndYesterdayDailiesResponse {
  observedDailies: ObservedDaily[]
  yesterdayDailies: ObservedDaily[]
}

export interface StationPrediction {
  abbreviation: ModelType
  bias_adjusted_relative_humidity: number | null
  bias_adjusted_temperature: number | null
  datetime: string
  precip_24hours: number | null
  id: string
  relative_humidity: number | null
  station: Station
  temperature: number | null
  wind_direction: number | null
  wind_speed: number | null
}

export enum ForecastActionChoice {
  CREATE = 'Create Forecast',
  EDIT = 'View/Edit Forecast'
}

export type ForecastActionType = 'Create Forecast' | 'View/Edit Forecast'

export const ForecastActionChoices: ForecastActionType[] = [ForecastActionChoice.CREATE, ForecastActionChoice.EDIT]

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
}

interface MoreCast2ForecastRecordResponse {
  forecasts: MoreCast2ForecastRecord[]
}

const marshalMoreCast2ForecastRecords = (forecasts: MoreCast2ForecastRow[]) => {
  const forecastRecords: MoreCast2ForecastRecord[] = forecasts.map(forecast => {
    return {
      station_code: forecast.stationCode,
      for_date: forecast.forDate.toMillis(),
      precip: forecast.precip.value,
      rh: forecast.rh.value,
      temp: forecast.temp.value,
      wind_direction: forecast.windDirection.value,
      wind_speed: forecast.windSpeed.value
    }
  })
  return forecastRecords
}

/**
 * POSTs a batch of forecasts.
 * @param forecasts The raw forecast model data.
 * @returns True if the response is a 201, otherwise false.
 */
export async function submitMoreCastForecastRecords(forecasts: MoreCast2ForecastRow[]): Promise<boolean> {
  const forecastRecords = marshalMoreCast2ForecastRecords(forecasts)
  const url = `/morecast-v2/forecast`
  try {
    const { status } = await axios.post<MoreCast2ForecastRecord[]>(url, {
      forecasts: forecastRecords
    })
    return status === 201
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (error: any) {
    console.error(error.message || error)
    return false
  }
}

/**
 * Retrieve a batch of forecasts for a specified date range and array of stations
 * @param startDate The start of the date range
 * @param endDate The end of the date range (inclusive)
 * @param stations The stations of interest
 */
export async function getMoreCast2ForecastRecordsByDateRange(
  startDate: DateTime,
  endDate: DateTime,
  stations: number[]
): Promise<MoreCast2ForecastRecord[]> {
  const url = `/morecast-v2/forecasts/${startDate.toISODate()}/${endDate.toISODate()}`
  const { data } = await axios.post<MoreCast2ForecastRecordResponse>(url, {
    stations
  })
  return data.forecasts
}

/**
 * Get noon model predictions for the specified date range
 * @param stationCodes A list of station codes of interest
 * @param model The weather model abbreviation
 * @param startDate The first date for which predictions will be returned
 * @param endDate The last date for which predictions will be returned
 */
export async function getModelPredictions(
  stationCodes: number[],
  model: ModelType,
  startDate: string,
  endDate: string
): Promise<StationPrediction[]> {
  if (stationCodes.length === 0) {
    return []
  }
  const url = `/weather_models/${model}/predictions/most_recent/${startDate}/${endDate}`
  const { data } = await axios.post<StationPrediction[]>(url, {
    stations: stationCodes
  })

  return data.map(d => ({ ...d, id: rowIDHasher(d.station.code, DateTime.fromISO(d.datetime)) }))
}

export async function getObservedDailies(
  stationCodes: number[],
  startDate: string,
  endDate: string
): Promise<ObservedDailyResponse[]> {
  if (stationCodes.length === 0) {
    return []
  }
  const url = `/morecast-v2/observed-dailies/${startDate}/${endDate}`
  const { data } = await axios.post<ObservedDailiesResponse>(url, {
    station_codes: stationCodes
  })

  return data.dailies
}

export async function getWeatherIndeterminates(
  stationCodes: number[],
  startDate: DateTime,
  endDate: DateTime
): Promise<StationWeatherIndeterminateResponse> {
  if (stationCodes.length === 0) {
    return {
      actuals: [],
      forecasts: [],
      predictions: []
    }
  }

  // Convert DateTime objects to strings

  return fakeData
}

const today = DateTime.now().startOf('day')
const fakeData = {
  actuals: [
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.minus({ days: 3 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.5,
      relative_humidity: 65,
      temperature: 3.7,
      wind_direction: 45,
      wind_speed: 15
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.minus({ days: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.9,
      relative_humidity: 75,
      temperature: 2.2,
      wind_direction: 60,
      wind_speed: 10
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.minus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 45,
      temperature: 4.1,
      wind_direction: 75,
      wind_speed: 5
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.toISODate() + 'T20:00:00+00:00',
      precipitation: null,
      relative_humidity: null,
      temperature: null,
      wind_direction: null,
      wind_speed: null
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.minus({ days: 3 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.5,
      relative_humidity: 65,
      temperature: 3.7,
      wind_direction: 45,
      wind_speed: 15
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.minus({ days: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.9,
      relative_humidity: 75,
      temperature: 2.2,
      wind_direction: 60,
      wind_speed: 10
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.minus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 45,
      temperature: 4.1,
      wind_direction: 75,
      wind_speed: 5
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.toISODate() + 'T20:00:00+00:00',
      precipitation: null,
      relative_humidity: null,
      temperature: null,
      wind_direction: null,
      wind_speed: null
    }
  ],
  forecasts: [],
  predictions: [
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.minus({ days: 3 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 50,
      temperature: 1.2,
      wind_direction: 125,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.minus({ days: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 75,
      temperature: 1.9,
      wind_direction: 90,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.minus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 35,
      temperature: 3.7,
      wind_direction: 125,
      wind_speed: 10
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 85,
      temperature: 3.2,
      wind_direction: 145,
      wind_speed: 5
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.plus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.7,
      relative_humidity: 55,
      temperature: 1.2,
      wind_direction: null,
      wind_speed: 0
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.minus({ days: 3 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 50,
      temperature: 1.2,
      wind_direction: 125,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.minus({ days: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 75,
      temperature: 1.9,
      wind_direction: 90,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.minus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 35,
      temperature: 3.7,
      wind_direction: 125,
      wind_speed: 10
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 85,
      temperature: 3.2,
      wind_direction: 145,
      wind_speed: 5
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.plus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.7,
      relative_humidity: 55,
      temperature: 1.2,
      wind_direction: null,
      wind_speed: 0
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.minus({ days: 3 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 50,
      temperature: 1.2,
      wind_direction: 125,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.minus({ days: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 75,
      temperature: 1.9,
      wind_direction: 90,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.minus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 35,
      temperature: 3.7,
      wind_direction: 125,
      wind_speed: 10
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 85,
      temperature: 3.2,
      wind_direction: 145,
      wind_speed: 5
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.plus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.7,
      relative_humidity: 55,
      temperature: 1.2,
      wind_direction: null,
      wind_speed: 0
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.minus({ days: 3 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 50,
      temperature: 1.2,
      wind_direction: 125,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.minus({ days: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 75,
      temperature: 1.9,
      wind_direction: 90,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.minus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 35,
      temperature: 3.7,
      wind_direction: 125,
      wind_speed: 10
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 85,
      temperature: 3.2,
      wind_direction: 145,
      wind_speed: 5
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.plus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.7,
      relative_humidity: 55,
      temperature: 1.2,
      wind_direction: null,
      wind_speed: 0
    }
  ]
}

const fakeDataBackup = {
  actuals: [
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.minus({ days: 3 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.5,
      relative_humidity: 65,
      temperature: 3.7,
      wind_direction: 45,
      wind_speed: 15
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.minus({ days: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.9,
      relative_humidity: 75,
      temperature: 2.2,
      wind_direction: 60,
      wind_speed: 10
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.minus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 45,
      temperature: 4.1,
      wind_direction: 75,
      wind_speed: 5
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.toISODate() + 'T20:00:00+00:00',
      precipitation: null,
      relative_humidity: null,
      temperature: null,
      wind_direction: null,
      wind_speed: null
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.minus({ days: 3 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.5,
      relative_humidity: 65,
      temperature: 3.7,
      wind_direction: 45,
      wind_speed: 15
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.minus({ days: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.9,
      relative_humidity: 75,
      temperature: 2.2,
      wind_direction: 60,
      wind_speed: 10
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.minus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 45,
      temperature: 4.1,
      wind_direction: 75,
      wind_speed: 5
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.ACTUAL,
      utc_timestamp: today.toISODate() + 'T20:00:00+00:00',
      precipitation: null,
      relative_humidity: null,
      temperature: null,
      wind_direction: null,
      wind_speed: null
    }
  ],
  forecasts: [],
  predictions: [
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.minus({ days: 3 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 50,
      temperature: 1.2,
      wind_direction: 125,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.minus({ days: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 75,
      temperature: 1.9,
      wind_direction: 90,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.minus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 35,
      temperature: 3.7,
      wind_direction: 125,
      wind_speed: 10
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 85,
      temperature: 3.2,
      wind_direction: 145,
      wind_speed: 5
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.plus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.7,
      relative_humidity: 55,
      temperature: 1.2,
      wind_direction: null,
      wind_speed: 0
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.plus({ day: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0,
      relative_humidity: 70,
      temperature: 2.2,
      wind_direction: null,
      wind_speed: 0
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.minus({ days: 3 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 50,
      temperature: 1.2,
      wind_direction: 125,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.minus({ days: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 75,
      temperature: 1.9,
      wind_direction: 90,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.minus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 35,
      temperature: 3.7,
      wind_direction: 125,
      wind_speed: 10
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 85,
      temperature: 3.2,
      wind_direction: 145,
      wind_speed: 5
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.plus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.7,
      relative_humidity: 55,
      temperature: 1.2,
      wind_direction: null,
      wind_speed: 0
    },
    {
      id: '',
      station_code: 322,
      station_name: 'Afton',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.plus({ day: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0,
      relative_humidity: 70,
      temperature: 2.2,
      wind_direction: null,
      wind_speed: 0
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.minus({ days: 3 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 50,
      temperature: 1.2,
      wind_direction: 125,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.minus({ days: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 75,
      temperature: 1.9,
      wind_direction: 90,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.minus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 35,
      temperature: 3.7,
      wind_direction: 125,
      wind_speed: 10
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 85,
      temperature: 3.2,
      wind_direction: 145,
      wind_speed: 5
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.plus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.7,
      relative_humidity: 55,
      temperature: 1.2,
      wind_direction: null,
      wind_speed: 0
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GDPS,
      utc_timestamp: today.plus({ day: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0,
      relative_humidity: 70,
      temperature: 2.2,
      wind_direction: null,
      wind_speed: 0
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.minus({ days: 3 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 50,
      temperature: 1.2,
      wind_direction: 125,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.minus({ days: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 75,
      temperature: 1.9,
      wind_direction: 90,
      wind_speed: 20
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.minus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.0,
      relative_humidity: 35,
      temperature: 3.7,
      wind_direction: 125,
      wind_speed: 10
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.toISODate() + 'T20:00:00+00:00',
      precipitation: 0.1,
      relative_humidity: 85,
      temperature: 3.2,
      wind_direction: 145,
      wind_speed: 5
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.plus({ days: 1 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0.7,
      relative_humidity: 55,
      temperature: 1.2,
      wind_direction: null,
      wind_speed: 0
    },
    {
      id: '',
      station_code: 317,
      station_name: 'Allison Pass',
      determinate: WeatherDeterminate.GFS,
      utc_timestamp: today.plus({ day: 2 }).toISODate() + 'T20:00:00+00:00',
      precipitation: 0,
      relative_humidity: 70,
      temperature: 2.2,
      wind_direction: null,
      wind_speed: 0
    }
  ]
}
