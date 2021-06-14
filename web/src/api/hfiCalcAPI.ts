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
}

export interface PlanningArea {
  id: number
  name: string
  fire_centre: FireCentre
}

export interface WeatherStation {
  code: number
  station_props: WeatherStationProperties
  planning_area: PlanningArea
}

export async function getHFIStations(): Promise<WeatherStation[]> {
  const url = '/hfi-calc/fire-centres'
  const { data } = await axios.get(url)

  return data.stations
}
