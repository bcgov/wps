import axios from 'api/axios'
import { FireSeason } from 'api/percentileAPI'

export interface WeatherStation {
  code: number
  name: string
  lat: number
  long: number
  ecodivision_name: string | null
  core_season: FireSeason
}

export interface Station {
  type: string
  properties: StationProperties
  geometry: StationGeometry
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
  features: Station[]
}

export enum StationSource {
  unspecified = 'unspecified',
  local_storage = 'local_storage',
  wildfire_one = 'wildfire_one'
}

export async function getStations(
  source: StationSource = StationSource.unspecified
): Promise<Station[]> {
  const url = '/stations/'
  const { data } = await axios.get<StationsResponse>(url, { params: { source } })

  return data.features
}
