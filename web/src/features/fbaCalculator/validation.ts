import { FBCTableRow } from 'features/fbaCalculator/RowManager'
import _ from 'lodash'
import { isNull } from 'lodash'

/**
 * Returns whether grass cure percentage input is invalid or not
 * @param row the input row to check against
 * @returns true if grass cure percentage is invalid, false otherwise
 */
export const isGrassCureInvalid = (row: FBCTableRow): boolean => {
  if (_.isUndefined(row)) {
    return false
  }

  let notSet = false
  if (row.fuelType?.value === 'o1a' || row.fuelType?.value === 'o1b') {
    notSet = _.isUndefined(row.grassCure) || isNaN(row.grassCure)
  }
  return notSet || isGreaterThan(row.grassCure)
}

/**
 * Returns whether wind speed input is invalid or not
 * @param row the input row to check against
 * @returns true if wind speed is greater than 100 (km/hr), false otherwise
 */
export const isWindSpeedInvalid = (windSpeed: number | undefined): boolean => {
  if (_.isUndefined(windSpeed)) {
    return false
  }
  return isGreaterThan(windSpeed, 120)
}

export const isGreaterThan = (input: number | undefined, limit = 100): boolean => {
  if (!_.isUndefined(input) && !isNull(input)) {
    return input > limit
  }
  return false
}
