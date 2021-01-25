import axios from 'api/axios'
import { FeatureCollection } from 'geojson'
import { API_BASE_URL } from 'utils/env'
import { ModelInfo } from 'api/modelAPI'

export interface ModelRun {
  model: ModelInfo
  model_run_timestamp: string
  prediction_timestamps: string[]
}

export interface ModelRuns {
  model_runs: ModelRun[]
}

export async function getModelRuns(
  model_run_timestamp: string | null
): Promise<ModelRuns> {
  const url = `${API_BASE_URL}/c-haines/model-runs`
  // console.log('API_BASE_URL', API_BASE_URL)
  // console.log(url)
  const { data } = await axios.get(url, {
    params: {
      model_run_timestamp: model_run_timestamp
        ? new Date(model_run_timestamp).toISOString()
        : null
    }
  })
  return data
}

export async function getCHainesGeoJSON(
  model: string,
  model_run_timestamp: string,
  prediction_timestamp: string
): Promise<FeatureCollection> {
  // console.log('fetching c-haines', model_run_timestamp, prediction_timestamp)
  // console.log('API_BASE_URL', API_BASE_URL)
  const url = `${API_BASE_URL}/c-haines/${model}/`
  console.log(url)
  const { data } = await axios.get(url, {
    params: { model_run_timestamp, prediction_timestamp }
  })
  return data
}
