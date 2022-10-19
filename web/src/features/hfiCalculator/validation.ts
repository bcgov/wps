import { StationDaily, FuelType } from 'api/hfiCalculatorAPI'
import { isEqual, isNull, isUndefined } from 'lodash'

export const isValidGrassCure = (daily: StationDaily | undefined, fuelType: FuelType | undefined): boolean => {
  if (!isGrassFuelType(fuelType)) {
    return true
  }
  return (
    !isUndefined(daily) &&
    !isNull(daily.grass_cure_percentage) &&
    !isUndefined(daily.grass_cure_percentage) &&
    !isNaN(daily.grass_cure_percentage)
  )
}

export const isGrassFuelType = (fuelType: FuelType | undefined): boolean => {
  if (isUndefined(fuelType)) {
    return false
  }
  return (
    isEqual(fuelType.abbrev.toLowerCase(), 'o1a') ||
    isEqual(fuelType.abbrev.toLowerCase(), 'o1b') ||
    isEqual(fuelType.abbrev.toLowerCase(), 'c7b')
  )
}
