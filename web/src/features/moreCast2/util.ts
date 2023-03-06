import { difference, groupBy, isEmpty, isNumber, sortBy } from 'lodash'
import { DateTime, Interval } from 'luxon'
import { FireCenterStation } from 'api/fbaAPI'
import { ModelChoice, ModelType, StationPrediction, YesterdayDaily } from 'api/moreCast2API'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'

// Convert the model predictions from the API to a format that can be used by a MoreCast2DataGrid data grid
export const parseModelsForStationsHelper = (predictions: StationPrediction[]): MoreCast2ForecastRow[] => {
  const rows: MoreCast2ForecastRow[] = []

  predictions.forEach(prediction => {
    const station_code = prediction.station.code
    const station_name = prediction.station.name
    const model = prediction.model
    const row: MoreCast2ForecastRow = {
      id: prediction.id,
      forDate: DateTime.fromISO(prediction.datetime),
      precip: {
        choice: model,
        value: isNumber(prediction.precip_24hours) ? prediction.precip_24hours : NaN
      },
      rh: {
        choice: model,
        value: isNumber(prediction.relative_humidity) ? prediction.relative_humidity : NaN
      },
      stationCode: station_code,
      stationName: station_name,
      temp: {
        choice: model,
        value: isNumber(prediction.temperature) ? prediction.temperature : NaN
      },
      windDirection: {
        choice: model,
        value: isNumber(prediction.wind_direction) ? prediction.wind_direction : NaN
      },
      windSpeed: {
        choice: model,
        value: isNumber(prediction.wind_speed) ? prediction.wind_speed : NaN
      }
    }
    rows.push(row)
  })
  return rows.sort((a, b) => a.stationName.localeCompare(b.stationName))
}

export const parseYesterdayDailiesForStationsHelper = (yesterdayDailies: YesterdayDaily[]): MoreCast2ForecastRow[] => {
  const rows: MoreCast2ForecastRow[] = []

  yesterdayDailies.forEach(daily => {
    const station_code = daily.station_code
    const station_name = daily.station_name
    const model = ModelChoice.YESTERDAY
    const row: MoreCast2ForecastRow = {
      id: daily.id,
      forDate: DateTime.fromISO(daily.utcTimestamp),
      precip: {
        choice: model,
        value: isNumber(daily.precipitation) ? daily.precipitation : NaN
      },
      rh: {
        choice: model,
        value: isNumber(daily.relative_humidity) ? daily.relative_humidity : NaN
      },
      stationCode: station_code,
      stationName: station_name,
      temp: {
        choice: model,
        value: isNumber(daily.temperature) ? daily.temperature : NaN
      },
      windDirection: {
        choice: model,
        value: isNumber(daily.wind_direction) ? daily.wind_direction : NaN
      },
      windSpeed: {
        choice: model,
        value: isNumber(daily.wind_speed) ? daily.wind_speed : NaN
      }
    }
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
  yesterdayDailies: YesterdayDaily[],
  dateInterval: string[]
): YesterdayDaily[] => {
  const expectedDates = dateInterval.map(date => DateTime.fromISO(date))

  const yesterdayDailiesExtendedToDateRange: YesterdayDaily[] = []

  // Dictionary of stationId -> daily, in theory there should be one yesterday daily for each station
  const yesterdayDailiesByStation = groupBy(yesterdayDailies, daily => daily.station_code)

  // Fill in missing values for stations that have at least one
  for (const stationCode in yesterdayDailiesByStation) {
    const dailies = sortBy(yesterdayDailiesByStation[stationCode], daily => DateTime.fromISO(daily.utcTimestamp))

    const dailyDates = dailies.map(daily => DateTime.fromISO(daily.utcTimestamp))
    const missingDates = difference(expectedDates, dailyDates)

    const yesterdayDaily = dailies[0]
    const missingDailies: YesterdayDaily[] = missingDates.map(date => ({
      ...yesterdayDaily,
      id: window.crypto.randomUUID(),
      utcTimestamp: date.toISO()
    }))
    yesterdayDailiesByStation[stationCode] = [...dailies, ...missingDailies]
    yesterdayDailiesExtendedToDateRange.push(...dailies, ...missingDailies)
  }

  // Fill in NA dailies for stations that don't have yesterday dailies
  const expectedStationIds = stations.map(station => station.code)
  const stationIdsWithDailies = yesterdayDailies.map(daily => daily.station_code)
  const missingStationIds = new Set(difference(expectedStationIds, stationIdsWithDailies))
  const missingStations = stations.filter(station => missingStationIds.has(station.code))

  const missingYesterdayDailies: YesterdayDaily[] = missingStations.flatMap(station =>
    dateInterval.map(date => ({
      id: window.crypto.randomUUID(),
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

  const completeYesterdayDailies = [...yesterdayDailiesExtendedToDateRange, ...missingYesterdayDailies]
  if (!isEmpty(dateInterval)) {
    return completeYesterdayDailies.filter(daily => DateTime.fromISO(daily.utcTimestamp) >= expectedDates[0])
  }
  return completeYesterdayDailies
}

export const fillInTheModelBlanks = (
  stations: FireCenterStation[],
  stationPredictions: StationPrediction[],
  dateInterval: string[],
  modelType: ModelType
) => {
  const missingPredictions: StationPrediction[] = []
  // Iterate through all the station codes and the expected date strings to ensure there is an
  // item in the array for each unique combination
  stations.forEach(station => {
    dateInterval.forEach(date => {
      const filteredPrediction = stationPredictions.filter(p => p.station.code === station.code && p.datetime === date)
      if (!filteredPrediction.length) {
        missingPredictions.push(createEmptyStationPrediction(station.code, date, station.name, modelType))
      }
    })
  })
  // Use .slice() to create a shallow copy of the predictions from the API and add the missing predictions
  const completeStationPredictions: StationPrediction[] = [...missingPredictions, ...stationPredictions.slice()]
  return completeStationPredictions
}

const createEmptyStationPrediction = (
  code: number,
  datetime: string,
  name: string,
  modelType: ModelType
): StationPrediction => {
  const prediction = {
    bias_adjusted_relative_humidity: NaN,
    bias_adjusted_temperature: NaN,
    datetime: datetime,
    precip_24hours: NaN,
    id: window.crypto.randomUUID(),
    model: modelType,
    relative_humidity: NaN,
    station: {
      code,
      name,
      lat: NaN,
      long: NaN,
      ecodivision_name: null,
      core_season: {
        start_month: NaN,
        start_day: NaN,
        end_month: NaN,
        end_day: NaN
      }
    },
    temperature: NaN,
    wind_direction: NaN,
    wind_speed: NaN
  }

  return prediction
}

export const createDateInterval = (fromDate: DateTime, toDate: DateTime) => {
  // Create an array of UTC datetime strings inclusive of the user selected from/to dates
  // This range of UTC datetimes is needed to help determine when a station is missing a
  // row of predictions
  const interval = Interval.fromDateTimes(fromDate, toDate.plus({ days: 1 }))
  const dateTimeArray = interval.splitBy({ day: 1 }).map(d => d.start)
  const dates = dateTimeArray.map(date => {
    return `${date.toISODate()}T20:00:00+00:00`
  })
  return dates
}
