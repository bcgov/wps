import { difference, differenceWith, groupBy, isEmpty, isEqual, isNumber, sortBy } from 'lodash'
import { DateTime } from 'luxon'
import { ModelChoice, ObservedDaily, ObservedDailyResponse } from 'api/moreCast2API'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'
import { FireCenterStation } from 'api/fbaAPI'
import { buildMoreCast2ForecastRow, rowIDHasher } from 'features/moreCast2/util'
import { ColYesterdayDailies } from 'features/moreCast2/slices/columnYesterdaySlice'

export const parseYesterdayDailiesFromResponse = (yesterdayDailiesResponse: ObservedDailyResponse[]): ObservedDaily[] =>
  yesterdayDailiesResponse.map(daily => ({
    ...daily,
    id: rowIDHasher(daily.station_code, DateTime.fromISO(daily.utcTimestamp)),
    data_type: 'YESTERDAY'
  }))

export const parseYesterdayDailiesForStationsHelper = (yesterdayDailies: ObservedDaily[]): MoreCast2ForecastRow[] => {
  const rows: MoreCast2ForecastRow[] = []

  yesterdayDailies.forEach(daily => {
    const model = ModelChoice.YESTERDAY
    const row = buildMoreCast2ForecastRow(daily, model)
    rows.push(row)
  })
  return rows.sort((a, b) => a.stationName.localeCompare(b.stationName))
}

/**
 *
 * Each station that has a daily for yesterday has that daily extended to the whole of the date range.
 *
 * Each station that does not have a daily gets filled with default N/A dailies.
 *
 * @param stations stations for the fire centre we expect yesterday dailies for
 * @param yesterdayDailies the yesterday dailies we received from the API
 * @param dateInterval the dates we expect to have yesterday dailies for each station
 */
export const fillInTheYesterdayDailyBlanks = (
  stations: FireCenterStation[],
  yesterdayDailies: ObservedDaily[],
  dateInterval: string[]
): ObservedDaily[] => {
  const expectedDates = dateInterval.map(date => DateTime.fromISO(date))

  const yesterdayDailiesExtendedToDateRange = extendDailiesForStations(yesterdayDailies, expectedDates)

  const missingYesterdayDailies: ObservedDaily[] = defaultsForMissingDailies(stations, yesterdayDailies, dateInterval)

  const completeYesterdayDailies = [...yesterdayDailiesExtendedToDateRange, ...missingYesterdayDailies]
  if (!isEmpty(dateInterval)) {
    return completeYesterdayDailies.filter(daily => DateTime.fromISO(daily.utcTimestamp) >= expectedDates[0])
  }
  return completeYesterdayDailies
}

/**
 * For stations that have dailies for yesterday, extend that daily to the rest of the range
 * @param yesterdayDailies the dailies for yesterday
 * @param expectedDates the date range
 * @returns existing dailies for yesterday and dailies for the rest of the range
 */
export const extendDailiesForStations = (yesterdayDailies: ObservedDaily[], expectedDates: DateTime[]) => {
  const yesterdayDailiesExtendedToDateRange: ObservedDaily[] = []

  // Dictionary of stationId -> daily, in theory there should be one yesterday daily for each station
  const yesterdayDailiesByStation = groupBy(yesterdayDailies, daily => daily.station_code)

  // Fill in missing values for stations that have at least one
  for (const stationCode in yesterdayDailiesByStation) {
    const dailies = sortBy(yesterdayDailiesByStation[stationCode], daily => DateTime.fromISO(daily.utcTimestamp))

    const dailyDates = dailies.map(daily => DateTime.fromISO(daily.utcTimestamp))
    const missingDates = differenceWith(expectedDates, dailyDates, isEqual)

    const yesterdayDaily = dailies[0]
    const missingDailies: ObservedDaily[] = missingDates.map(date => ({
      ...yesterdayDaily,
      id: rowIDHasher(yesterdayDaily.station_code, date),
      utcTimestamp: date.toISO()
    }))
    yesterdayDailiesByStation[stationCode] = [...dailies, ...missingDailies]
    yesterdayDailiesExtendedToDateRange.push(...dailies, ...missingDailies)
  }
  return yesterdayDailiesExtendedToDateRange
}
/**
 *  Fill in NA dailies for stations that don't have yesterday dailies
 * @param stations
 * @param yesterdayDailies
 * @param dateInterval
 * @returns default yesterday dailies for stations that have no dailies
 */
export const defaultsForMissingDailies = (
  stations: FireCenterStation[],
  yesterdayDailies: ObservedDaily[],
  dateInterval: string[]
): ObservedDaily[] => {
  const expectedStationIds = stations.map(station => station.code)
  const stationIdsWithDailies = yesterdayDailies.map(daily => daily.station_code)
  const missingStationIds = new Set(difference(expectedStationIds, stationIdsWithDailies))
  const missingStations = stations.filter(station => missingStationIds.has(station.code))

  const missingYesterdayDailies: ObservedDaily[] = missingStations.flatMap(station =>
    dateInterval.map(date => ({
      id: rowIDHasher(station.code, DateTime.fromISO(date)),
      data_type: 'YESTERDAY',
      station_code: station.code,
      station_name: station.name,
      utcTimestamp: date,
      temperature: null,
      relative_humidity: null,
      precipitation: null,
      wind_direction: null,
      wind_speed: null
    }))
  )
  return missingYesterdayDailies
}

export const replaceColumnValuesFromYesterdayDaily = (
  existingRows: MoreCast2ForecastRow[],
  fireCentreStations: FireCenterStation[],
  dateInterval: string[],
  colYesterdayDaily: ColYesterdayDailies
) => {
  const completeDailies = fillInTheYesterdayDailyBlanks(
    fireCentreStations,
    colYesterdayDaily.yesterdayDailies,
    dateInterval
  )
  const morecast2ForecastRows = parseYesterdayDailiesForStationsHelper(completeDailies)

  return existingRows.flatMap(row => {
    const newPred = morecast2ForecastRows.find(pred => pred.id === row.id)
    if (newPred) {
      return {
        ...row,
        [colYesterdayDaily.colField]: newPred[colYesterdayDaily.colField]
      }
    } else {
      return {
        ...row,
        [colYesterdayDaily.colField]: { value: NaN, choice: colYesterdayDaily.modelType }
      }
    }
  })
}
