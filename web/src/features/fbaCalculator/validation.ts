import _ from 'lodash'
import { isNull } from 'lodash'
import { FBAInputRow } from './components/FBAInputGrid'

/**
 * Returns whether grass cure percentage input is invalid or not
 * @param row the input row to check against
 * @returns true if grass cure percentage is invalid, false otherwise
 */
export const isGrassCureInvalid = (row: FBAInputRow): boolean => {
  if (_.isUndefined(row)) {
    return false
  }

  let notSet = false
  if (row.fuelType === 'o1a' || row.fuelType === 'o1b') {
    notSet = _.isUndefined(row.grassCure) || isNaN(row.grassCure)
  }
  return notSet || isGreaterThan100(row.grassCure)
}

/**
 * Returns whether wind speed input is invalid or not
 * @param row the input row to check against
 * @returns true if wind speed is greater than 100 (km/hr), false otherwise
 */
export const isWindSpeedInvalid = (row: FBAInputRow): boolean => {
  if (_.isUndefined(row)) {
    return false
  }
  return isGreaterThan100(row.windSpeed)
}

export const isGreaterThan100 = (input: number | undefined): boolean => {
  if (!_.isUndefined(input) && !isNull(input)) {
    return input > 100
  }
  return false
}
