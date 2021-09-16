import { WeatherStationProperties } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { isEqual, isNull, isUndefined } from 'lodash'

export const isValidGrassCure = (
  daily: StationDaily | undefined,
  stationProperties: WeatherStationProperties
): boolean => {
  if (!isGrassFuelType(stationProperties)) {
    return true
  }
  return (
    !isUndefined(daily) &&
    !isNull(daily.grass_cure_percentage) &&
    !isUndefined(daily.grass_cure_percentage) &&
    !isNaN(daily.grass_cure_percentage)
  )
}

export const isGrassFuelType = (stationProperties: WeatherStationProperties): boolean => {
  return (
    isEqual(stationProperties.fuel_type.abbrev.toLowerCase(), 'o1a') ||
    isEqual(stationProperties.fuel_type.abbrev.toLowerCase(), 'o1b')
  )
}
