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

export interface HFIWeatherStationsResponse {
    fire_centres: FireCentre[]
    planning_areas_by_fire_centre: Record<string, PlanningArea[]>
    stations_by_planning_area: Record<string, WeatherStation[]>
}

export async function getHFIStations(): Promise<HFIWeatherStationsResponse> {
  const url = '/hfi-calc/fire-centres'
  const { data } = await axios.get(url)

  return data.stations
}
