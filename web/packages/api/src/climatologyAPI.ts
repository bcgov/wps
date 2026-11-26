import axios from './axios'

export type ClimatologyVariable =
  | 'temperature'
  | 'relative_humidity'
  | 'wind_speed'
  | 'precipitation'
  // The FWI System indices, as WF1 calculated them.
  | 'ffmc'
  | 'dmc'
  | 'dc'
  | 'isi'
  | 'bui'
  | 'fwi'

// How several stations are combined: the mean of the stations each day, every station's value
// pooled into one distribution, or a climatology for each station.
export type ClimatologyMethod = 'average' | 'pooled' | 'each'

// How a variable has been distributed on one day of the year, over the reference years.
export interface ClimatologyDay {
  month: number
  day: number
  // How many values the distribution is drawn from: years, or station years when pooled.
  count: number
  // How many stations contributed to it.
  station_count: number
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
  // One station's value, or the mean of the stations that reported.
  value: number
  station_count: number
}

// The stations' daily values in a year the selected year is compared with.
export interface ClimatologyYear {
  year: number
  observations: ClimatologyObservation[]
}

// A daily climatology for some stations, and their values in the selected year.
export interface ClimatologySeries {
  station_codes: number[]
  // The years the distribution is drawn from, which leave out the selected year. Null with no
  // history.
  first_reference_year: number | null
  last_reference_year: number | null
  days: ClimatologyDay[]
  observations: ClimatologyObservation[]
  // The years asked for to compare with. The distribution includes them.
  compared_years: ClimatologyYear[]
}

// One series when the stations are combined, or one per station.
export interface DailyClimatology {
  variable: ClimatologyVariable
  year: number
  method: ClimatologyMethod
  series: ClimatologySeries[]
}

export interface ClimatologyStation {
  code: number
  name: string
  // The fire zone, such as K2, when WF1 has one.
  zone: string | null
}

export interface ClimatologyFireCentre {
  id: number
  name: string
  stations: ClimatologyStation[]
}

export async function getDailyClimatology(
  stationCodes: number[],
  variable: ClimatologyVariable,
  year: number,
  method: ClimatologyMethod,
  compareYears: number[]
): Promise<DailyClimatology> {
  const { data } = await axios.get<DailyClimatology>('/climatology/daily', {
    params: { station_codes: stationCodes, variable, year, method, compare_years: compareYears },
    // The API reads a list as a repeated parameter: station_codes=1&station_codes=2
    paramsSerializer: { indexes: null }
  })
  return data
}

export async function getClimatologyFireCentres(): Promise<ClimatologyFireCentre[]> {
  const { data } = await axios.get<{ fire_centres: ClimatologyFireCentre[] }>('/climatology/fire-centres')
  return data.fire_centres
}
