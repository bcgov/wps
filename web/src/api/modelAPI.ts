import axios from 'api/axios'
import { Station } from 'api/stationAPI'

export interface ModelSummary {
  datetime: string
  tmp_tgl_2_5th: number
  tmp_tgl_2_median: number
  tmp_tgl_2_90th: number
  rh_tgl_2_5th: number
  rh_tgl_2_median: number
  rh_tgl_2_90th: number
}

interface ModelInfo {
  name: string
  abbrev: string
}

// List of model summaries for each datetime with model & station info
export interface ModelSummariesForStation {
  station: Station
  model: ModelInfo | null
  values: ModelSummary[]
}

export interface ModelSummariesResponse {
  summaries: ModelSummariesForStation[]
}

/**
 * Get the past model prediction percentiles (5th & 90th)
 * @param stationCodes A list of requested station codes
 * @param model Type of Env canada weather model
 */
export async function getModelSummaries(
  stationCodes: number[],
  model: 'GDPS' | 'HRDPS' | 'RDPS'
): Promise<ModelSummariesForStation[]> {
  const url = `/models/${model}/predictions/summaries/`
  const { data } = await axios.post<ModelSummariesResponse>(url, {
    stations: stationCodes
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
  wind_direction: number | null
  wind_speed: number | null
  total_precipitation: number | null
  dew_point: number | null
  cloud_cover: number
  sea_level_pressure: number
  wind_speed_40m: number
  wind_direction_40m: number
  wind_direction_80m: number
  wind_speed_120m: number
  wind_direction_120m: number
  wind_speed_925mb: number
  wind_direction_925mb: number
  wind_speed_850mb: number
  wind_direction_850m: number
}

export interface Model {
  station: Station
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
  station: Station
  model_runs: ModelRun[]
}

export interface BiasAdjModelResponse {
  stations: ModelsForStation[]
}

/**
 * Get the past and future model predictions that are adjusted based on learned biases
 * @param stationCodes A list of requested station codes
 * @param model Type of Env canada weather model
 */
export async function getModelsWithBiasAdj(
  stationCodes: number[],
  model: 'GDPS' | 'HRDPS' | 'RDPS'
): Promise<ModelsForStation[]> {
  const url = `/models/${model}/predictions/most_recent/`
  const { data } = await axios.post<BiasAdjModelResponse>(url, {
    stations: stationCodes
  })

  return data.stations
}
