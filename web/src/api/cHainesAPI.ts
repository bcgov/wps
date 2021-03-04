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
  // console.log('fetching c-haines', model_run_timestamp, prediction_timestamp)
  // console.log('API_BASE_URL', API_BASE_URL)
  const url = `${API_BASE_URL}/c-haines/${model}/prediction`
  console.log(url)
  const { data } = await axios.get(url, {
    params: { model_run_timestamp, prediction_timestamp }
  })
  return data
}

export async function getFireCentresGeoJSON(): Promise<FeatureCollection> {
  // NOTE: This should rather be loaded as a vector tileset. The entire
  // dataset is about 21MB big, and probably slow things down terribly.
  const url =
    'https://openmaps.gov.bc.ca/geo/pub/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&outputFormat=json&typeName=WHSE_LEGAL_ADMIN_BOUNDARIES.DRP_MOF_FIRE_CENTRES_SP&srsName=EPSG:4326'
  const { data } = await axios.get(url)
  return data
}
