import axios from 'api/axios'
import { Station } from 'api/stationAPI'
import { rowIDHasher } from 'features/moreCast2/util'
import { isEqual } from 'lodash'

export enum ModelChoice {
  GDPS = 'GDPS',
  GFS = 'GFS',
  HRDPS = 'HRDPS',
  NAM = 'NAM',
  RDPS = 'RDPS',
  MANUAL = 'MANUAL',
  YESTERDAY = 'YESTERDAY'
}
export const DEFAULT_MODEL_TYPE: ModelType = ModelChoice.HRDPS

export interface YesterdayDailiesResponse {
  dailies: YesterdayDailyResponse[]
}

export interface YesterdayDailyResponse {
  station_code: number
  station_name: string
  utcTimestamp: string
  temperature: number | null
  relative_humidity: number | null
  precipitation: number | null
  wind_direction: number | null
  wind_speed: number | null
}

export interface YesterdayDaily extends YesterdayDailyResponse {
  id: string
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

export type ModelType = 'HRDPS' | 'GDPS' | 'GFS' | 'YESTERDAY' | 'NAM' | 'RDPS' | 'MANUAL'

export const ModelChoices: ModelType[] = [
  ModelChoice.GDPS,
  ModelChoice.GFS,
  ModelChoice.HRDPS,
  ModelChoice.YESTERDAY,
  ModelChoice.MANUAL,
  ModelChoice.NAM,
  ModelChoice.RDPS
]

export const ModelOptions: ModelType[] = ModelChoices.filter(choice => !isEqual(choice, ModelChoice.MANUAL))

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

  return data.map(d => ({ ...d, id: rowIDHasher(d.station.code, d.datetime) }))
}

/**
 * Get noon yesterday dailies for the specified date
 * @param stationCodes A list of station codes of interest
 * @param startDate The first date for which we ask for the day before
 */
export async function getYesterdayDailies(
  stationCodes: number[],
  startDate: string
): Promise<YesterdayDailyResponse[]> {
  if (stationCodes.length === 0) {
    return []
  }
  const url = `/morecast-v2/yesterday-dailies/${startDate}`
  const { data } = await axios.post<YesterdayDailiesResponse>(url, {
    station_codes: stationCodes
  })

  return data.dailies
}
