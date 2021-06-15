import axios from 'api/axios'

export interface FuelType {
  abbrev: string
  description: string
}

export interface WeatherStationProperties {
  name: string
  elevation: number | null
  uuid: string
  fuel_type: FuelType
}

export interface FireCentre {
  id: number
  name: string
  planning_areas: PlanningArea[]
}

export interface PlanningArea {
  id: number
  name: string
  stations: WeatherStation[]
}

export interface WeatherStation {
  code: number
  station_props: WeatherStationProperties
}

export interface HFIWeatherStationsResponse {
  fire_centres: FireCentre[]
}

export async function getHFIStations(): Promise<HFIWeatherStationsResponse> {
  const url = '/hfi-calc/fire-centres'
  const { data } = await axios.get(url)

  return data
}
