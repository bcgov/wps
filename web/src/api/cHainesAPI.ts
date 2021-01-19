import axios from 'api/axios'
import { FeatureCollection } from 'geojson'

export interface ModelRun {
  model_run_timestamp: string
  prediction_timestamps: string[]
}

export interface ModelRuns {
  model_runs: ModelRun[]
}

export async function getModelRuns(): Promise<ModelRuns> {
  const url = '/c-haines/model-runs/'
  const { data } = await axios.get(url)
  return data
}

export async function getCHainesGeoJSON(
  model_run_timestamp: string,
  prediction_timestamp: string
): Promise<FeatureCollection> {
  console.log('fetching c-haines', model_run_timestamp, prediction_timestamp)
  const url = '/c-haines/'
  const { data } = await axios.get(url, {
    params: { model_run_timestamp, prediction_timestamp }
  })
  return data
}
