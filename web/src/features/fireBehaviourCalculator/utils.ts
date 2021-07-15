import assert from 'assert'
import _ from 'lodash'
import { isNull } from 'lodash'
import { FBCInputRow } from './components/FBCInputGrid'

export const isGrassFuelType = (fuelType: string): boolean =>
  fuelType === 'o1a' || fuelType === 'o1b'
export const isValidFuelSetting = (
  fuelType: string,
  grassCurePercentage: number | null
): boolean => {
  if (isGrassFuelType(fuelType)) {
    return !isNull(grassCurePercentage)
  }
  return true
}
/**
 * Extracts search params from url and marshalls them into rows for the fire behaviour calculator
 * @param searchParams Form is ?s=<station-code>&f=<fuel-type>&c=<grass-cure-percentage>,...
 * @returns
 */
export const getRowsFromUrlParams = (searchParams: string): FBCInputRow[] => {
  const buildRow = (params: string[]) => {
    // station, fuel type, grass cure %
    if (params.length !== 3 && params.length !== 4) {
      // malformed param query
      return null
    }
    assert(params.length === 3 || params.length === 4)

    const rowToBuild = {
      weatherStation: '1',
      fuelType: 'c1',
      grassCure: 0,
      windSpeed: 0.0
    }
    params.forEach(param => {
      const keyValPair = param.replace('?', '').split('=')
      assert(keyValPair.length === 2)
      switch (keyValPair[0]) {
        case 's':
          rowToBuild.weatherStation = keyValPair[1]
          break
        case 'f':
          rowToBuild.fuelType = keyValPair[1]
          break
        case 'c':
          rowToBuild.grassCure = parseInt(keyValPair[1])
          break
        case 'w':
          rowToBuild.windSpeed = parseFloat(keyValPair[1])
          break
        default:
          // No op
          break
      }
    })
    return rowToBuild
  }
  if (_.isEmpty(searchParams)) {
    return []
  }
  const rows = searchParams.split(',').flatMap((param, index) => {
    const individualParams = param.split('&')
    const builtRow = buildRow(individualParams)
    if (_.isNull(builtRow)) {
      return []
    }
    const rowWithId = {
      id: index,
      weatherStation: builtRow.weatherStation,
      fuelType: builtRow.fuelType,
      grassCure: builtRow.grassCure,
      windSpeed: builtRow.windSpeed
    }
    return rowWithId
  })
  return rows
}

/**
 * Complement of getRowsFromUrlParams
 * @param rows FBCInputRow array from data table
 * @returns params as string of form ?s=<station-code>&f=<fuel-type>&c=<grass-cure-percentage>&w=<optional-wind-speed>,...
 */
export const getUrlParamsFromRows = (rows: FBCInputRow[]): string => {
  if (rows.length === 0) {
    return ''
  }
  const query = '?'
  const params = rows
    .map(
      row =>
        `s=${row.weatherStation}&f=${row.fuelType}&c=${row.grassCure}&w=${row.windSpeed}`
    )
    .join(',')

  return query + params
}

export const getMostRecentIdFromRows = (rows: FBCInputRow[]): number => {
  let lastIdFromExisting = _.maxBy(rows, 'id')?.id
  lastIdFromExisting = lastIdFromExisting ? lastIdFromExisting : 0
  const lastId = _.isEmpty(rows) ? 0 : lastIdFromExisting
  return lastId
}
