import {
  WIND_DIRECTION_VALUES_DECIMAL,
  WIND_SPEED_VALUES_DECIMAL,
  WIND_SPEED_FORECAST_VALUES_DECIMAL,
  TEMPERATURE_VALUES_DECIMAL,
  PRECIP_VALUES_DECIMAL,
  RH_VALUES_DECIMAL,
  DEW_POINT_VALUES_DECIMAL
} from 'utils/constants'

export function formatWindDirection(
  wind_direction: number | undefined | null
): string | undefined {
  if (typeof wind_direction === 'number') {
    return wind_direction.toFixed(WIND_DIRECTION_VALUES_DECIMAL).padStart(3, '0')
  }
  return undefined
}

export function formatWindSpeed(
  wind_speed: number | undefined | null
): string | undefined {
  if (typeof wind_speed === 'number') {
    return wind_speed.toFixed(WIND_SPEED_VALUES_DECIMAL)
  }
  return undefined
}

export function formatForecastWindSpeed(
  wind_speed: number | undefined | null
): string | undefined {
  if (typeof wind_speed === 'number') {
    return wind_speed.toFixed(WIND_SPEED_FORECAST_VALUES_DECIMAL)
  }
  return undefined
}

export function formatTemperature(
  temperature: number | undefined | null
): string | undefined {
  if (typeof temperature === 'number') {
    return temperature.toFixed(TEMPERATURE_VALUES_DECIMAL)
  }
  return undefined
}

export function formatRelativeHumidity(
  relative_humidity: number | undefined | null
): string | undefined {
  if (typeof relative_humidity === 'number') {
    return relative_humidity.toFixed(RH_VALUES_DECIMAL)
  }
  return undefined
}

export function formatPrecipitation(
  precipitation: number | undefined | null
): string | undefined {
  if (typeof precipitation === 'number') {
    return precipitation.toFixed(PRECIP_VALUES_DECIMAL)
  }
  return undefined
}

export function formatDewPoint(dew_point: number | undefined | null): string | undefined {
  if (typeof dew_point === 'number') {
    return dew_point.toFixed(DEW_POINT_VALUES_DECIMAL)
  }
  return undefined
}
