import { Station } from 'api/stationAPI'
import axios from 'api/axios'

export interface ObservedValue {
  datetime: string
  temperature: number | null
  relative_humidity: number | null
  wind_speed: number | null
  wind_direction: number | null
  barometric_pressure: number | null
  precipitation: number | null
  ffmc: number | null
  isi: number | null
  fwi: number | null
}

export interface Observation {
  station: Station
  values: ObservedValue[]
}

export interface ObservationsResponse {
  hourlies: Observation[]
}

export async function getObservations(stationCodes: number[]): Promise<Observation[]> {
  const url = '/hourlies/'
  const { data } = await axios.post<ObservationsResponse>(url, {
    stations: stationCodes
  })

  return data.hourlies
}
