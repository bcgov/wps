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
  const { data } = await axios.get(url, {
    params: {
      model_run_timestamp: model_run_timestamp
        ? new Date(model_run_timestamp).toISOString()
        : null
    }
  })
  return data
}

export function getCHainesGeoJSONURI(
  model: string,
  model_run_timestamp: string,
  prediction_timestamp: string
): string {
  return `${API_BASE_URL}/c-haines/${encodeURIComponent(
    model
  )}/prediction?model_run_timestamp=${encodeURIComponent(
    model_run_timestamp
  )}&prediction_timestamp=${encodeURIComponent(prediction_timestamp)}`
}

export function getKMLNetworkLinkURI(): string {
  return `${API_BASE_URL}/c-haines/network-link`
}

export function getCHainesModelKMLURI(model: string): string {
  return `${API_BASE_URL}/c-haines/${encodeURIComponent(
    model
  )}/predictions?response_format=KML`
}

export function getCHainesKMLURI(
  model: string,
  model_run_timestamp: string,
  prediction_timestamp: string
): string {
  return `${API_BASE_URL}/c-haines/${encodeURIComponent(
    model
  )}/prediction?model_run_timestamp=${encodeURIComponent(
    model_run_timestamp
  )}&prediction_timestamp=${encodeURIComponent(prediction_timestamp)}&response_format=KML`
}

export function getCHainesKMLModelRunURI(
  model: string,
  model_run_timestamp: string
): string {
  return `${API_BASE_URL}/c-haines/${encodeURIComponent(
    model
  )}/predictions?model_run_timestamp=${encodeURIComponent(
    model_run_timestamp
  )}&response_format=KML`
}

export async function getCHainesGeoJSON(
  model: string,
  model_run_timestamp: string,
  prediction_timestamp: string
): Promise<FeatureCollection> {
  const url = `${API_BASE_URL}/c-haines/${model}/prediction`
  const { data } = await axios.get(url, {
    params: { model_run_timestamp, prediction_timestamp }
  })
  return data
}
