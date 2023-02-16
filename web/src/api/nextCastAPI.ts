import axios from 'api/axios'
import { Station } from 'api/stationAPI'

export enum ModelChoice {
  GDPS = 'GDPS',
  GFS = 'GFS',
  HRDPS = 'HRDPS',
  NAMM = 'NAMM',
  RDPS = 'RDPS',
  MANUAL = 'MANUAL'
}

interface PredictionValues {
  precip: number
  rh: number
  temp: number
  wind_direction: number
  wind_speed: number
}

interface StationPrediction {
  date: number
  model: ModelType
  station: Station
  values: PredictionValues
}

interface ModelPredictionResponse {
  predictions: StationPrediction[]
}

type ModelType = 'HRDPS' | 'GDPS' | 'GFS' | 'NAMM' | 'RDPS'

/**
 * Get noon model predictions for the specified date range
 * @param stationCodes A list of station codes of interest
 * @param model The weather model abbreviation
 * @param from_date The first date (epoch time) for which predictions will be returned
 * @param to_date The last date (epoch time) for which predictions will be returned
 */
export async function getModelPredictions(
  stationCodes: number[],
  model: ModelType,
  fromDate: number,
  toDate: number
): Promise<StationPrediction[]> {
  const url = `/weather_models/${model}/forecast/noon/predictions`
  const { data } = await axios.post<ModelPredictionResponse>(url, {
    stations: stationCodes,
    from_date: fromDate,
    to_date: toDate
  })

  return data.predictions
}
