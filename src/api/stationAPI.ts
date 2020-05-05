import axios from 'api/axios'

export interface Station {
  code: number
  name: string
  lat: string
  long: string
}

export interface StationsResponse {
  weather_stations: Station[]
}

export async function getStations(): Promise<Station[]> {
  const url = '/stations/'

  try {
    const { data } = await axios.get<StationsResponse>(url)
    return data.weather_stations
  } catch (err) {
    throw err.toString()
  }
}
