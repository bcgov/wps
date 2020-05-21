import { Station } from 'api/stationAPI'
import axios from 'api/axios'

interface HourlyReading {
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

export interface HourlyReadings {
  station: Station
  values: HourlyReading[]
}

export interface HourliesResponse {
  hourlies: HourlyReadings[]
}

export async function getHourlies(stationCodes: number[]): Promise<HourlyReadings[]> {
  const url = '/hourlies/'

  try {
    const { data } = await axios.post<HourliesResponse>(url, {
      stations: stationCodes
    })
    return data.hourlies
  } catch (err) {
    throw err.toString()
  }
}
