import { DateTime, Interval } from 'luxon'
import { ModelChoice, MoreCast2ForecastRecord, WeatherDeterminate } from 'api/moreCast2API'
import { MoreCast2ForecastRow, MoreCast2Row } from 'features/moreCast2/interfaces'
import { StationGroupMember } from 'api/stationAPI'
import { groupBy, isUndefined } from 'lodash'
import { getDateTimeNowPST } from 'utils/date'
import { isForecastRowPredicate } from 'features/moreCast2/saveForecasts'
import { bui, dc, dmc, ffmc, fwi, isi } from 'utils/fwi'

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
      },
      grassCuring: {
        choice: ModelChoice.FORECAST,
        value: forecast.grass_curing
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

export const isForecastRow = (row: MoreCast2Row) => {
  return !rowContainsActual(row) && !isBeforeToday(row.forDate)
}

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
      row.grassCuringForecast = matchingRow.grassCuringForecast
    }
  }
  return newRows
}

export const fillForecastsFromRows = (
  rowsToFill: MoreCast2Row[],
  savedRows: MoreCast2Row[] | undefined
): MoreCast2Row[] => {
  if (savedRows) {
    const savedRowsMap = getRowsMap(savedRows)
    rowsToFill
      .filter(row => isForecastRow(row))
      .map(forecastRow => {
        const savedRow = savedRowsMap.get(forecastRow.id)
        if (savedRow) {
          forecastRow.tempForecast = savedRow.tempForecast
          forecastRow.rhForecast = savedRow.rhForecast
          forecastRow.windDirectionForecast = savedRow.windDirectionForecast
          forecastRow.windSpeedForecast = savedRow.windSpeedForecast
          forecastRow.precipForecast = savedRow.precipForecast
          forecastRow.grassCuringForecast = savedRow.grassCuringForecast
          forecastRow.ffmcCalcForecast = savedRow.ffmcCalcForecast
          forecastRow.dmcCalcForecast = savedRow.dmcCalcForecast
          forecastRow.dcCalcForecast = savedRow.dcCalcForecast
          forecastRow.isiCalcForecast = savedRow.isiCalcForecast
          forecastRow.buiCalcForecast = savedRow.buiCalcForecast
          forecastRow.fwiCalcForecast = savedRow.fwiCalcForecast
        }
      })
  }
  return rowsToFill
}

/**
 * Fills all stations grass curing values with the last entered value for each station
 * @param rows - MoreCast2Row[]
 * @returns MoreCast2Row[]
 */
export const fillGrassCuringCWFIS = (rows: MoreCast2Row[]): MoreCast2Row[] => {
  const stationGrassMap = new Map<number, { date: DateTime; grassCuringCWFIS: number }>()
  // Iterate through all rows first so we know we have all the CWFIS grass curing values for each station
  // regardless of row order.
  for (const row of rows) {
    const { stationCode, forDate, grassCuringCWFIS } = row
    const grassCuring = grassCuringCWFIS && !isNaN(grassCuringCWFIS.value) ? grassCuringCWFIS.value : NaN

    if (!isNaN(grassCuring)) {
      const existingStation = stationGrassMap.get(stationCode)

      if (!existingStation || forDate > existingStation.date) {
        stationGrassMap.set(stationCode, { date: forDate, grassCuringCWFIS: grassCuring })
      }
    }
  }

  for (const row of rows) {
    const stationInfo = stationGrassMap.get(row.stationCode)
    // Fill the grass curing CWFIS value as long as it doesn't already have a value.
    if (stationInfo && row.grassCuringCWFIS && isNaN(row.grassCuringCWFIS.value) && row.forDate > stationInfo.date) {
      row.grassCuringCWFIS.value = stationInfo.grassCuringCWFIS
    }
  }
  return rows
}

/**
 * Fills all stations grass curing values with the last entered value for each station
 * @param rows - MoreCast2Row[]
 * @returns MoreCast2Row[]
 */
export const fillGrassCuringForecast = (rows: MoreCast2Row[]): MoreCast2Row[] => {
  const stationGrassMap = new Map<number, { date: DateTime; grassCuring: number }>()
  // iterate through all rows first so we know we have all the grass curing values for each station
  // regardless of row order
  for (const row of rows) {
    const { stationCode, forDate, grassCuringForecast, grassCuringActual } = row

    const grassCuring =
      grassCuringForecast && !isNaN(grassCuringForecast.value) ? grassCuringForecast.value : grassCuringActual

    if (!isNaN(grassCuring)) {
      const existingStation = stationGrassMap.get(stationCode)

      if (!existingStation || forDate > existingStation.date) {
        stationGrassMap.set(stationCode, { date: forDate, grassCuring: grassCuring })
      }
    }
  }

  for (const row of rows) {
    const stationInfo = stationGrassMap.get(row.stationCode)
    // fill the grass curing forecast value, as long as it doesn't already have a value
    if (
      stationInfo &&
      row.grassCuringForecast &&
      isNaN(row.grassCuringForecast.value) &&
      row.forDate > stationInfo.date
    ) {
      row.grassCuringForecast.value = stationInfo.grassCuring
    }
  }
  return rows
}

/**
 * Provided a single row for a station is edited, fills all grass curing values for that station
 * forward in time.
 * @param editedRow - MoreCast2Row
 * @param allRows - MoreCast2Row[]
 * @returns MoreCast2Row[]
 */
export const fillStationGrassCuringForward = (editedRow: MoreCast2Row, allRows: MoreCast2Row[]) => {
  const editedStationCode = editedRow.stationCode
  const editedDate = editedRow.forDate
  const newGrassCuringValue = editedRow.grassCuringForecast!.value
  const stationRows = allRows.filter(row => row.stationCode === editedStationCode)

  for (const row of stationRows) {
    if (row.forDate > editedDate) {
      row.grassCuringForecast!.value = newGrassCuringValue
    }
  }
  return stationRows
}

/**
 * Checks if a datetime object is before the start of today
 * @param datetime
 * @returns boolean
 */
export const isBeforeToday = (datetime: DateTime): boolean => {
  const today = getDateTimeNowPST().startOf('day')

  return datetime < today
}

export const rowContainsActual = (row: MoreCast2Row): boolean => {
  return Object.entries(row).some(
    ([key, value]) => key.includes(WeatherDeterminate.ACTUAL) && typeof value === 'number' && !isNaN(value)
  )
}

export const getRowsMap = (morecastRows: MoreCast2Row[]): Map<string, MoreCast2Row> => {
  const morecastRowMap = new Map<string, MoreCast2Row>()
  morecastRows.forEach((row: MoreCast2Row) => {
    morecastRowMap.set(row.id, row)
  })
  return morecastRowMap
}

export const simulateFireWeatherIndices = (rows: MoreCast2Row[]): MoreCast2Row[] => {
  // Group all the rows by stationCode and sort each array of group members by date
  const groupedByStation = groupBy(rows, 'stationCode')
  for (const values of Object.values(groupedByStation)) {
    values.sort((a, b) => dateTimeComparator(a.forDate, b.forDate))
  }

  for (const key of Object.keys(groupedByStation)) {
    const group = groupedByStation[key]
    // If we only have 0 or 1 forecasts in the group it isn't possible to simulate indices
    if (group.length < 2) {
      continue
    }
    // Iterate through the forecasts in the group in pairs, using a previous actual/forecast
    // as the basis simulating indices of the current forecast
    for (let i = 1; i < group.length; i++) {
      const previous = group[i - 1]
      const current = group[i]
      if (!isForecastRowPredicate(current)) {
        // No need to simulate indices for actuals
        continue
      }

      const updatedForecast = calculateFWIs(previous, current)
      group[i] = updatedForecast
    }
  }
  // Merge all the forecasts in the group back into a single array.
  let result: MoreCast2Row[] = []
  for (const key of Object.keys(groupedByStation)) {
    result = [...result, ...groupedByStation[key]]
  }
  return result
}

export const calculateFWIs = (previous: MoreCast2Row, current: MoreCast2Row): MoreCast2Row => {
  const month = current.forDate.month
  const latitude = current.latitude
  const temp = current.tempForecast
  const rh = current.rhForecast
  const precip = current.precipForecast
  const windSpeed = current.windSpeedForecast

  const previousFfmc = isForecastRowPredicate(previous) ? previous.ffmcCalcForecast?.value : previous.ffmcCalcActual
  const previousDmc = isForecastRowPredicate(previous) ? previous.dmcCalcForecast?.value : previous.dmcCalcActual
  const previousDc = isForecastRowPredicate(previous) ? previous.dcCalcForecast?.value : previous.dcCalcActual

  if (previousFfmc) {
    const simulatedFfmc = ffmc(previousFfmc, temp!.value, rh!.value, windSpeed!.value, precip!.value)
    current.ffmcCalcForecast = { choice: ModelChoice.NULL, value: simulatedFfmc }
  }
  if (previousDmc) {
    const simulatedDmc = dmc(previousDmc, temp!.value, rh!.value, precip!.value, latitude, month, true)
    current.dmcCalcForecast = { choice: ModelChoice.NULL, value: simulatedDmc }
  }
  if (previousDc) {
    const simulatedDc = dc(previousDc, temp!.value, rh!.value, precip!.value, latitude, month, true)
    current.dcCalcForecast = { choice: ModelChoice.NULL, value: simulatedDc }
  }
  if (!isUndefined(current.ffmcCalcForecast?.value)) {
    const simulatedIsi = isi(current.ffmcCalcForecast.value, windSpeed!.value, false)
    current.isiCalcForecast = { choice: ModelChoice.NULL, value: simulatedIsi }
  }
  if (!isUndefined(current.dmcCalcForecast?.value) && !isUndefined(current.dcCalcForecast?.value)) {
    const simulatedBui = bui(current.dmcCalcForecast.value, current.dcCalcForecast.value)
    current.buiCalcForecast = { choice: ModelChoice.NULL, value: simulatedBui }
  }
  if (!isUndefined(current.isiCalcForecast?.value) && !isUndefined(current.buiCalcForecast?.value)) {
    const simulatedFwi = fwi(current.isiCalcForecast.value, current.buiCalcForecast.value)
    current.fwiCalcForecast = { choice: ModelChoice.NULL, value: simulatedFwi }
  }

  return current
}

/**
 * Compares two luxon DateTime objects for sorting purposes.
 * @param a A luxon DateTime.
 * @param b A luxon DateTime
 * @returns -1 if a is earlier than b, 1 if a is later than b and 0 if a and b are the same
 */
export const dateTimeComparator = (a: DateTime, b: DateTime): number => {
  if (a < b) {
    return -1
  }
  if (a > b) {
    return 1
  }
  return 0
}
