import {
  WIND_DIRECTION_VALUES_DECIMAL,
  WIND_SPEED_VALUES_DECIMAL,
  WIND_SPEED_FORECAST_VALUES_DECIMAL,
  TEMPERATURE_VALUES_DECIMAL,
  PRECIP_VALUES_DECIMAL,
  RH_VALUES_DECIMAL,
  DEW_POINT_VALUES_DECIMAL
} from 'utils/constants'

export function formatWindDirection(wind_direction: number): string {
  return wind_direction.toFixed(WIND_DIRECTION_VALUES_DECIMAL).padStart(3, '0')
}

export function formatWindSpeed(wind_speed: number): string {
  return wind_speed.toFixed(WIND_SPEED_VALUES_DECIMAL)
}

export function formatForecastWindSpeed(wind_speed: number): string {
  return wind_speed.toFixed(WIND_SPEED_FORECAST_VALUES_DECIMAL)
}

export function formatTemperature(temperature: number): string {
  return temperature.toFixed(TEMPERATURE_VALUES_DECIMAL)
}

export function formatRelativeHumidity(relative_humidity: number): string {
  return relative_humidity.toFixed(RH_VALUES_DECIMAL)
}

export function formatPrecipitation(precipitation: number): string {
  return precipitation.toFixed(PRECIP_VALUES_DECIMAL)
}

export function formatDewPoint(dew_point: number): string {
  return dew_point.toFixed(DEW_POINT_VALUES_DECIMAL)
}
