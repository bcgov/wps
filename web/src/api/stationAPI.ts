import axios from 'api/axios'
import { FireSeason } from 'api/percentileAPI'

export interface Station {
  code: number
  name: string
  lat: number
  long: number
  ecodivision_name: string | null
  core_season: FireSeason
}

export interface GeoJsonStation {
  type: string
  properties: StationProperties
  geometry: StationGeometry
}

export interface DetailedGeoJsonStation {
  type: string
  properties: DetailedStationProperties
  geometry: StationGeometry
}

export interface DetailedStationProperties extends StationProperties {
  observations: {
    temperature: number
    relative_humidity: number
  }
  forecasts: {
    temperature: number
    relative_humidity: number
  }
}
export interface StationProperties {
  code: number
  name: string
  ecodivision_name: string | null
  core_season: FireSeason
}

export interface StationGeometry {
  type: string
  coordinates: number[]
}

export interface StationsResponse {
  type: string
  features: GeoJsonStation[]
}

export interface DetailedStationsResponse {
  type: string
  features: DetailedGeoJsonStation[]
}

export enum StationSource {
  unspecified = 'unspecified',
  local_storage = 'local_storage',
  wildfire_one = 'wildfire_one'
}

const url = '/stations/'

export async function getStations(
  source: StationSource = StationSource.unspecified
): Promise<GeoJsonStation[]> {
  const { data } = await axios.get<StationsResponse>(url, { params: { source } })

  return data.features
}

export async function getDetailedStations(): Promise<DetailedGeoJsonStation[]> {
  const detailedUrl = `${url}details/`
  const { data } = await axios.get<DetailedStationsResponse>(detailedUrl, {})

  return data.features
}
