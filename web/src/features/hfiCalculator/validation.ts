import { WeatherStationProperties } from 'api/hfiCalcAPI'
import { isEqual } from 'lodash'

export const isGrassFuelType = (stationProperties: WeatherStationProperties): boolean => {
  return (
    isEqual(stationProperties.fuel_type.abbrev.toLowerCase(), 'o1a') ||
    isEqual(stationProperties.fuel_type.abbrev.toLowerCase(), 'o1b')
  )
}
