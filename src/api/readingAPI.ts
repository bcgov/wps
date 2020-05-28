import { Station } from 'api/stationAPI'
import axios from 'api/axios'

export interface ReadingValue {
  datetime: string
  temperature: number
  relative_humidity: number
  wind_speed: number
  wind_direction: number
  barometric_pressure: number
  precipitation: number
  ffmc?: number
  isi?: number
  fwi?: number
}

export interface Reading {
  station: Station
  values: ReadingValue[]
}

export interface ReadingsResponse {
  hourlies: Reading[]
}

export async function getReadings(stationCodes: number[]): Promise<Reading[]> {
  const url = '/hourlies/'

  try {
    const { data } = await axios.post<ReadingsResponse>(url, {
      stations: stationCodes
    })
    return data.hourlies
  } catch (err) {
    throw err.toString()
  }
}
