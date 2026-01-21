/**
 * TypeScript interfaces for the Climatology feature
 */

export enum WeatherVariable {
  HOURLY_TEMPERATURE = 'HOURLY_TEMPERATURE',
  HOURLY_RELATIVE_HUMIDITY = 'HOURLY_RELATIVE_HUMIDITY',
  HOURLY_WIND_SPEED = 'HOURLY_WIND_SPEED',
  HOURLY_PRECIPITATION = 'HOURLY_PRECIPITATION',
  HOURLY_FFMC = 'HOURLY_FFMC',
  HOURLY_ISI = 'HOURLY_ISI',
  HOURLY_FWI = 'HOURLY_FWI'
}

export enum AggregationPeriod {
  DAILY = 'daily',
  MONTHLY = 'monthly'
}

export interface ReferencePeriod {
  start_year: number
  end_year: number
}

export interface ClimatologyRequest {
  station_code: number
  variable: WeatherVariable
  aggregation: AggregationPeriod
  reference_period: ReferencePeriod
  comparison_year?: number
}

export interface ClimatologyDataPoint {
  period: number // Day of year (1-366) or month (1-12)
  mean: number | null
  p10: number | null
  p25: number | null
  p50: number | null
  p75: number | null
  p90: number | null
}

export interface CurrentYearDataPoint {
  period: number // Day of year (1-366) or month (1-12)
  value: number | null
  date: string // YYYY-MM-DD
}

export interface StationInfo {
  code: number
  name: string
  elevation: number | null
}

export interface ClimatologyResponse {
  climatology: ClimatologyDataPoint[]
  current_year: CurrentYearDataPoint[]
  station: StationInfo
  variable: WeatherVariable
  aggregation: AggregationPeriod
  reference_period: ReferencePeriod
  comparison_year: number | null
}

// Display labels for weather variables
export const WEATHER_VARIABLE_LABELS: Record<WeatherVariable, string> = {
  [WeatherVariable.HOURLY_TEMPERATURE]: 'Temperature',
  [WeatherVariable.HOURLY_RELATIVE_HUMIDITY]: 'Relative Humidity',
  [WeatherVariable.HOURLY_WIND_SPEED]: 'Wind Speed',
  [WeatherVariable.HOURLY_PRECIPITATION]: 'Precipitation',
  [WeatherVariable.HOURLY_FFMC]: 'Fine Fuel Moisture Code (FFMC)',
  [WeatherVariable.HOURLY_ISI]: 'Initial Spread Index (ISI)',
  [WeatherVariable.HOURLY_FWI]: 'Fire Weather Index (FWI)'
}

// Units for weather variables
export const WEATHER_VARIABLE_UNITS: Record<WeatherVariable, string> = {
  [WeatherVariable.HOURLY_TEMPERATURE]: '°C',
  [WeatherVariable.HOURLY_RELATIVE_HUMIDITY]: '%',
  [WeatherVariable.HOURLY_WIND_SPEED]: 'km/h',
  [WeatherVariable.HOURLY_PRECIPITATION]: 'mm',
  [WeatherVariable.HOURLY_FFMC]: '',
  [WeatherVariable.HOURLY_ISI]: '',
  [WeatherVariable.HOURLY_FWI]: ''
}

// Standard climate normal reference periods
export const STANDARD_REFERENCE_PERIODS: ReferencePeriod[] = [
  { start_year: 1991, end_year: 2020 },
  { start_year: 1981, end_year: 2010 },
  { start_year: 1971, end_year: 2000 }
]
