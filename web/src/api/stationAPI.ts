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

export interface StationsResponse {
  weather_stations: Station[]
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

  return data.weather_stations
}
