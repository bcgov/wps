import axios from 'api/axios'
import { WeatherStation } from 'api/stationAPI'

export interface ModelSummary {
  datetime: string
  tmp_tgl_2_5th: number
  tmp_tgl_2_median: number
  tmp_tgl_2_90th: number
  rh_tgl_2_5th: number
  rh_tgl_2_median: number
  rh_tgl_2_90th: number
}

export interface ModelInfo {
  name: string
  abbrev: string
}

// List of model summaries for each datetime with model & station info
export interface ModelSummariesForStation {
  station: WeatherStation
  model: ModelInfo | null
  values: ModelSummary[]
}

export interface ModelSummariesResponse {
  summaries: ModelSummariesForStation[]
}

/**
 * Get the past model prediction percentiles (5th & 90th)
 * @param stationCodes A list of station codes of interest
 * @param model Available weather model type from Env Canada
 */
export async function getModelSummaries(
  stationCodes: number[],
  model: 'GDPS' | 'HRDPS' | 'RDPS',
  timeOfInterest: string
): Promise<ModelSummariesForStation[]> {
  const url = `/weather_models/${model}/predictions/summaries/`
  const { data } = await axios.post<ModelSummariesResponse>(url, {
    stations: stationCodes,
    time_of_interest: timeOfInterest
  })

  return data.summaries
}

interface ModelRunInfo {
  datetime: string
  name: string
  abbreviation: string
}

export interface ModelValue {
  datetime: string
  temperature: number | null
  bias_adjusted_temperature: number | null
  relative_humidity: number | null
  bias_adjusted_relative_humidity: number | null
  wind_direction?: number | null
  wind_speed?: number | null
  delta_precipitation?: number | null
  model_run_datetime?: string | null
}

export interface Model {
  station: WeatherStation
  values: ModelValue[]
}

export interface ModelsResponse {
  predictions: Model[]
}

export interface ModelRun {
  model_run: ModelRunInfo
  values: ModelValue[]
}

export interface ModelsForStation {
  station: WeatherStation
  model_runs: ModelRun[]
}

export interface BiasAdjModelResponse {
  stations: ModelsForStation[]
}

/**
 * Get model predictions with bias adjusted GDPS from past 5 days to future 10 days
 * @param stationCodes A list of station codes of interest
 * @param model Available weather model type from Env Canada
 */
export async function getModelsWithBiasAdj(
  stationCodes: number[],
  model: 'GDPS' | 'HRDPS' | 'RDPS',
  timeOfInterest: string
): Promise<ModelsForStation[]> {
  const url = `/weather_models/${model}/predictions/most_recent/`
  const { data } = await axios.post<BiasAdjModelResponse>(url, {
    stations: stationCodes,
    time_of_interest: timeOfInterest
  })

  return data.stations
}
