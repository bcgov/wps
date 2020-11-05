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

export async function getStations(): Promise<Station[]> {
  const url = '/stations/'
  const { data } = await axios.get<StationsResponse>(url)

  return data.weather_stations
}
