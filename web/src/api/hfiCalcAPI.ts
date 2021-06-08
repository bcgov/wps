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
    name: string
}

export interface PlanningArea {
    name: string
    fire_centre: FireCentre
}

export interface WeatherStation {
    code: number
    properties: WeatherStationProperties
    planning_area: PlanningArea
}

export async function getHFIStations(): Promise<WeatherStation[]> {
    const url = '/hfi-calc/'
    const { data } = await axios.get(url)

    return data.stations
}
