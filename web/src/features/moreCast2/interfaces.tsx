import { ModelChoice } from 'api/nextCastAPI'

export interface ForecastedPrecip {
  choice: ModelChoice
  precip: number
}

export interface ForecastedRH {
  choice: ModelChoice
  rh: number
}

export interface ForcastedTemperature {
  choice: ModelChoice
  temp: number
}

export interface ForecastedWindDirection {
  choice: ModelChoice
  wind_direction: number
}

export interface ForecastedWindSpeed {
  choice: ModelChoice
  wind_speed: number
}

export interface NextCastForecastRow {
  id: string
  for_date: number
  precip: ForecastedPrecip
  rh: ForecastedRH
  station_code: number
  station_name: string
  temp: ForcastedTemperature
  wind_direction: ForecastedWindDirection
  wind_speed: ForecastedWindSpeed
}
