import axios from 'api/axios'
import { Station } from 'api/stationAPI'

export interface ModelValue {
  datetime: string
  temperature: number
  relative_humidity: number
  wind_direction: number
  wind_speed: number
  total_precipitation: number
  dew_point: number
  accumulated_rain: number
  accumulated_snow: number
  accumulated_freezing_rain: number
  accumulated_ice_pellets: number
  cloud_cover: number
  sea_level_pressure: number
  wind_speed_40m: number
  wind_direction_40m: number
  wind_direction_80m: number
  wind_speed_120m: number
  wind_direction_120m: number
  wind_speed_925mb: number
  wind_direction_925mb: number
  wind_speed_850mb: number
  wind_direction_850m: number
}

export interface Model {
  station: Station
  values: ModelValue[]
}

export interface ModelsResponse {
  forecasts: Model[]
}

export async function getModels(stationCodes: number[]): Promise<Model[]> {
  const url = '/forecasts/'

  try {
    const { data } = await axios.post<ModelsResponse>(url, {
      stations: stationCodes
    })
    return data.forecasts
  } catch (err) {
    throw err.toString()
  }
}
