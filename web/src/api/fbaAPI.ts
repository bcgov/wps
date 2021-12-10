import axios from 'api/axios'
import { FuelTypes } from 'features/fbaCalculator/fuelTypes'
import { getStations, StationSource } from 'api/stationAPI'

export interface FireCenterStation {
  code: number
  name: string
  zone?: string
}

export interface FireBehaviourAdvisory {
  station_code: number
  zone_code: string
  fuel_type: FuelTypes
  grass_cure?: number
  wind_speed: number
  hfi: number
  ros: number
  thirty_min_fire_size: number
  sixty_min_fire_size: number
  fire_type: string
  critical_hours_4000?: string
  critical_hours_10000?: string
}

export interface FireCenter {
  id: number
  name: string
  stations: FireCenterStation[]
}

export interface FireCentersResponse {
  fire_centers: FireCenter[]
}

export interface FBAResponse {
  date: string
  fireBehaviourAdvisories: FireBehaviourAdvisory[]
}

export async function getFBAFireCenters(): Promise<FireCentersResponse> {
  const url = '/fba/fire-centers'

  const { data } = await axios.get(url, {})
  return data
}

export async function getFBAs(date: string): Promise<FBAResponse> {
  const url = '/fba-calc/stations'

  const allStations = await getStations(StationSource.wildfire_one, date)

  // const fireBehaviourStations = allStations.map(station => ({
  //   stationCode: station.properties.code,
  //   fuelType: 'C3' // TODO: remove. Temporarily using arbitrarily chosen fuel type for all stations
  // }))

  const fireBehaviourStations = [
    { station_code: allStations[3].properties.code, fuel_type: 'D1' }
  ]

  const { data } = await axios.post(url, {
    date: date,
    stations: fireBehaviourStations
  })
  return data
}
