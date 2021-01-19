import axios from 'api/axios'
import { FeatureCollection } from 'geojson'
import { API_BASE_URL } from 'utils/env'

export interface ModelRun {
  model_run_timestamp: string
  prediction_timestamps: string[]
}

export interface ModelRuns {
  model_runs: ModelRun[]
}

export async function getModelRuns(): Promise<ModelRuns> {
  const url = `${API_BASE_URL}/c-haines/model-runs/`
  console.log('API_BASE_URL', API_BASE_URL)
  console.log(url)
  const { data } = await axios.get(url)
  return data
}

export async function getCHainesGeoJSON(
  model_run_timestamp: string,
  prediction_timestamp: string
): Promise<FeatureCollection> {
  console.log('fetching c-haines', model_run_timestamp, prediction_timestamp)
  console.log('API_BASE_URL', API_BASE_URL)
  const url = `${API_BASE_URL}/c-haines/`
  console.log(url)
  const { data } = await axios.get(url, {
    params: { model_run_timestamp, prediction_timestamp }
  })
  return data
}
