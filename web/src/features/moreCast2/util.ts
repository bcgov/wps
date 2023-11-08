import { DateTime, Interval } from 'luxon'
import { ModelChoice, MoreCast2ForecastRecord } from 'api/moreCast2API'
import { MoreCast2ForecastRow, MoreCast2Row } from 'features/moreCast2/interfaces'
import { StationGroupMember } from 'api/stationAPI'
import { isUndefined } from 'lodash'

export const parseForecastsHelper = (
  forecasts: MoreCast2ForecastRecord[],
  stations: StationGroupMember[]
): MoreCast2ForecastRow[] => {
  const rows: MoreCast2ForecastRow[] = []

  forecasts.forEach(forecast => {
    const row: MoreCast2ForecastRow = {
      id: rowIDHasher(forecast.station_code, DateTime.fromMillis(forecast.for_date)),
      forDate: DateTime.fromMillis(forecast.for_date),
      precip: {
        choice: ModelChoice.FORECAST,
        value: forecast.precip
      },
      rh: {
        choice: ModelChoice.FORECAST,
        value: forecast.rh
      },
      stationCode: forecast.station_code,
      stationName: stations.find(station => station.station_code === forecast.station_code)?.display_label || '',
      temp: {
        choice: ModelChoice.FORECAST,
        value: forecast.temp
      },
      windDirection: {
        choice: ModelChoice.FORECAST,
        value: forecast.wind_direction || NaN
      },
      windSpeed: {
        choice: ModelChoice.FORECAST,
        value: forecast.wind_speed
      }
    }
    rows.push(row)
  })
  return rows
}

/**
 * Returns a unique ID by simply concatenating stationCode and timestamp
 * @param stationCode
 * @param timestamp
 * @returns String concatenation of stationCode and timestamp as an ID
 */
export const rowIDHasher = (stationCode: number, timestamp: DateTime) =>
  `${stationCode}${timestamp.startOf('day').toISODate()}`

export const createDateInterval = (fromDate: DateTime, toDate: DateTime) => {
  // Create an array of UTC datetime strings inclusive of the user selected from/to dates
  // This range of UTC datetimes is needed to help determine when a station is missing a
  // row of predictions
  const interval = Interval.fromDateTimes(fromDate, toDate.plus({ days: 1 }))
  const dateTimeArray = interval.splitBy({ day: 1 }).map(d => d.start)
  const dates = dateTimeArray.map(date => {
    return `${date?.toISODate()}T20:00:00+00:00`
  })
  return dates
}

export const createWeatherModelLabel = (label: string) => {
  if (label?.endsWith('_BIAS')) {
    const index = label.indexOf('_BIAS')
    const prefix = label.slice(0, index)
    return `${prefix} bias`
  }

  return label === ModelChoice.NULL ? '' : label
}

export const createLabel = (isActual: boolean, label: string) => {
  if (isActual) {
    return ModelChoice.ACTUAL
  }

  return createWeatherModelLabel(label)
}

export const validActualOrForecastPredicate = (row: MoreCast2Row) =>
  validForecastPredicate(row) || validActualPredicate(row)

export const validActualPredicate = (row: MoreCast2Row) =>
  !isNaN(row.precipActual) && !isNaN(row.rhActual) && !isNaN(row.tempActual) && !isNaN(row.windSpeedActual)

// A valid forecast row has values for precipForecast, rhForecast, tempForecast and windSpeedForecast
export const validForecastPredicate = (row: MoreCast2Row) =>
  !isUndefined(row.precipForecast) &&
  !isNaN(row.precipForecast.value) &&
  !isUndefined(row.rhForecast) &&
  !isNaN(row.rhForecast.value) &&
  !isUndefined(row.tempForecast) &&
  !isNaN(row.tempForecast.value) &&
  !isUndefined(row.windSpeedForecast) &&
  !isNaN(row.windSpeedForecast.value)

export const mapForecastChoiceLabels = (newRows: MoreCast2Row[], storedRows: MoreCast2Row[]): MoreCast2Row[] => {
  const storedRowChoicesMap = new Map<string, MoreCast2Row>()

  for (const row of storedRows) {
    storedRowChoicesMap.set(row.id, row)
  }

  for (const row of newRows) {
    const matchingRow = storedRowChoicesMap.get(row.id)
    if (matchingRow) {
      row.precipForecast = matchingRow.precipForecast
      row.tempForecast = matchingRow.tempForecast
      row.rhForecast = matchingRow.rhForecast
      row.windDirectionForecast = matchingRow.windDirectionForecast
      row.windSpeedForecast = matchingRow.windSpeedForecast
    }
  }
  return newRows
}
