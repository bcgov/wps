import { isUndefined } from 'lodash'
import { FBCInputRow } from './components/FBCInputGrid'

/**
 * Validates the input row if the fuel type is a grass fuel type
 *
 * @param row the row to validate
 * @returns false if valid, true otherwise
 */
export const grassCureNotSetForGrassType = (row: FBCInputRow): boolean => {
  if (isUndefined(row)) {
    return false
  }
  if (row.fuelType === 'o1a' || row.fuelType === 'o1b') {
    return isUndefined(row.grassCure) || isNaN(row.grassCure)
  }
  return false
}

/**
 * Validates the input row by requiring that station and fuel type are set
 *
 * @param row the row to validate
 * @returns false if valid, true otherwise
 */
export const shouldDisableCalculate = (row: FBCInputRow): boolean => {
  const grassCureNotSet = grassCureNotSetForGrassType(row)
  if (grassCureNotSet) {
    return true
  }
  return (
    isUndefined(row.weatherStation) ||
    row.weatherStation === 'undefined' ||
    isUndefined(row.fuelType) ||
    row.fuelType === 'undefined'
  )
}
