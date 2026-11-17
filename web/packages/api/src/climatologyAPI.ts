import axios from './axios'

export type ClimatologyVariable = 'temperature' | 'relative_humidity' | 'wind_speed' | 'precipitation'

// How a variable has been distributed on one day of the year, over the reference years.
export interface ClimatologyDay {
  month: number
  day: number
  count: number
  minimum: number
  p25: number
  median: number
  p75: number
  p90: number
  maximum: number
}

export interface ClimatologyObservation {
  // ISO date, e.g. 2026-07-01
  date: string
  value: number
}

// A station's daily climatology for a variable, and its values in one year to compare.
export interface DailyClimatology {
  station_code: number
  variable: ClimatologyVariable
  year: number
  // The years the distribution is drawn from, which leave out `year`. Null with no history.
  first_reference_year: number | null
  last_reference_year: number | null
  days: ClimatologyDay[]
  observations: ClimatologyObservation[]
}

export async function getDailyClimatology(
  stationCode: number,
  variable: ClimatologyVariable,
  year: number
): Promise<DailyClimatology> {
  const url = `/climatology/stations/${stationCode}/daily`
  const { data } = await axios.get<DailyClimatology>(url, { params: { variable, year } })
  return data
}
