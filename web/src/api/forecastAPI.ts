import axios from 'api/axios'
import { Station } from 'api/stationAPI'

export interface NoonForecastValue {
  datetime: string
  temperature: number
  relative_humidity: number
  wind_direction: number
  wind_speed: number
  total_precipitation: number
  gc: number
  ffmc: number
  dmc: number
  dc: number
  isi: number
  bui: number
  fwi: number
  danger_rating: number
  created_at: string
}

export interface Forecast {
  station_code: number
  values: NoonForecastValue[]
}

export interface ForecastResponse {
  noon_forecasts: Forecast[]
}

export async function getNoonForecasts(stationCodes: number[]): Promise<Forecast[]> {
  const url = '/noon_forecasts/'

  const { data } = await axios.post<ForecastResponse>(url, {
    stations: stationCodes
  })
  return data.noon_forecasts
}

export interface ForecastSummary {
  datetime: string
  tmp_min: number
  tmp_max: number
  rh_min: number
  rh_max: number
}

// List of noon forecast summaries for each datetime with station info
export interface ForecastSummariesForStation {
  station: Station
  values: ForecastSummary[]
}

export interface ForecastSummariesResponse {
  summaries: ForecastSummariesForStation[]
}

export async function getForecastSummaries(
  stationCodes: number[]
): Promise<ForecastSummariesForStation[]> {
  const url = `/noon_forecasts/summaries/`
  const { data } = await axios.post<ForecastSummariesResponse>(url, {
    stations: stationCodes
  })

  return data.summaries
}
