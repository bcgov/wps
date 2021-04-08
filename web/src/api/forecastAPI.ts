import axios from 'api/axios'
import { WeatherStation } from 'api/stationAPI'

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

export async function getNoonForecasts(
  stationCodes: number[],
  timeOfInterest: string
): Promise<Forecast[]> {
  const url = '/forecasts/noon/'

  const { data } = await axios.post<ForecastResponse>(url, {
    stations: stationCodes,
    time_of_interest: timeOfInterest
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
  station: WeatherStation
  values: ForecastSummary[]
}

export interface ForecastSummariesResponse {
  summaries: ForecastSummariesForStation[]
}

export async function getForecastSummaries(
  stationCodes: number[],
  timeOfInterest: string
): Promise<ForecastSummariesForStation[]> {
  const url = `/forecasts/noon/summaries/`
  const { data } = await axios.post<ForecastSummariesResponse>(url, {
    stations: stationCodes,
    time_of_interest: timeOfInterest
  })

  return data.summaries
}
