import axios from 'api/axios'
import { Station } from 'api/stationAPI'

export enum ModelChoice {
  GDPS = 'GDPS',
  GFS = 'GFS',
  HRDPS = 'HRDPS',
  NAM = 'NAM',
  RDPS = 'RDPS',
  MANUAL = 'MANUAL'
}

export interface StationPrediction {
  bias_adjusted_relative_humidity: number | null
  bias_adjusted_temperature: number | null
  datetime: string
  precip_24hours: number
  id: string
  model: ModelType
  relative_humidity: number
  station: Station
  temperature: number
  wind_direction: number
  wind_speed: number
}

export type ModelType = 'HRDPS' | 'GDPS' | 'GFS' | 'MANUAL' | 'NAM' | 'RDPS'

export const ModelChoices: ModelType[] = [
  ModelChoice.GDPS,
  ModelChoice.GFS,
  ModelChoice.HRDPS,
  ModelChoice.MANUAL,
  ModelChoice.NAM,
  ModelChoice.RDPS
]

/**
 * Get noon model predictions for the specified date range
 * @param stationCodes A list of station codes of interest
 * @param model The weather model abbreviation
 * @param fromDate The first date for which predictions will be returned
 * @param toDate The last date for which predictions will be returned
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

  return data
}
