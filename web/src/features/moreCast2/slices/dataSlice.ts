import { createSelector, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { RootState } from 'app/rootReducer'
import {
  fetchWeatherIndeterminates,
  ModelChoice,
  WeatherIndeterminate,
  WeatherIndeterminatePayload,
  WeatherDeterminate,
  WeatherDeterminateType
} from 'api/moreCast2API'
import { AppThunk } from 'app/store'
import { rowIDHasher } from 'features/moreCast2/util'
import { DateTime } from 'luxon'
import { logError } from 'utils/error'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { createDateInterval } from 'features/moreCast2/util'
import { isUndefined } from 'lodash'
import { selectSelectedStations } from 'features/moreCast2/slices/selectedStationsSlice'

interface State {
  loading: boolean
  error: string | null
  actuals: WeatherIndeterminate[]
  forecasts: WeatherIndeterminate[]
  predictions: WeatherIndeterminate[]
}

export const initialState: State = {
  loading: false,
  error: null,
  actuals: [],
  forecasts: [],
  predictions: []
}

const dataSlice = createSlice({
  name: 'DataSlice',
  initialState,
  reducers: {
    getWeatherIndeterminatesStart(state: State) {
      state.error = null
      state.actuals = []
      state.forecasts = []
      state.predictions = []
      state.loading = true
    },
    getWeatherIndeterminatesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getWeatherIndeterminatesSuccess(state: State, action: PayloadAction<WeatherIndeterminatePayload>) {
      state.error = null
      state.actuals = action.payload.actuals
      state.forecasts = action.payload.forecasts
      state.predictions = action.payload.predictions
      state.loading = false
    }
  }
})

export const { getWeatherIndeterminatesStart, getWeatherIndeterminatesFailed, getWeatherIndeterminatesSuccess } =
  dataSlice.actions

export default dataSlice.reducer

/**
 * Use the morecast2API to get WeatherIndeterminates from the backend. Fills in missing
 * actuals and predictions. Results are stored the Redux store.
 * @param stationCodes The list of station codes to retreive data for.
 * @param fromDate The start date from which to retrieve data from (inclusive).
 * @param toDate The end date from which to retrieve data from (inclusive).
 * @returns An array or WeatherIndeterminates.
 */
export const getWeatherIndeterminates =
  (stationCodes: number[], fromDate: DateTime, toDate: DateTime): AppThunk =>
  async dispatch => {
    try {
      dispatch(getWeatherIndeterminatesStart())
      const data = await fetchWeatherIndeterminates(stationCodes, fromDate, toDate)
      const actuals = fillMissingActuals(data.actuals, fromDate, toDate)
      const forecasts = fillMissingForecasts(data.forecasts, fromDate, toDate, stationCodes)
      const predictions = fillMissingPredictions(data.predictions, fromDate, toDate)
      const payload = {
        actuals: addUniqueIds(actuals),
        forecasts: addUniqueIds(forecasts),
        predictions: addUniqueIds(predictions)
      }
      dispatch(getWeatherIndeterminatesSuccess(payload))
    } catch (err) {
      dispatch(getWeatherIndeterminatesFailed((err as Error).toString()))
      logError(err)
    }
  }

/**
 * Replaces the existing ID, or adds a new ID to each item based on the item's
 * station_code and utc_timestamp.
 * @param items An array of WeatherIndeterminates to update.
 * @returns Returns an array of WeatherIndeterminates where each item has an ID derived
 * from its station_code and utc_timestamp.
 */
const addUniqueIds = (items: WeatherIndeterminate[]) => {
  return items.map(item => ({
    ...item,
    id: rowIDHasher(item.station_code, DateTime.fromISO(item.utc_timestamp))
  }))
}

/**
 * Given an array of WeatherIndeterminates and a date range, ensure an actual is present for each
 * day for each station code.
 * @param items An array of WeatherIndeterminates that may need additional empty actuals added.
 * @param fromDate The start date for which actuals are required (inclusive).
 * @param toDate The end date for which actuals are required (inclusive).
 * @returns An array of WeatherIndeterminates with all required actuals are present. Actuals may
 * contain NaN values for dates in the future or dates where the backend does not provide data.
 */
const fillMissingActuals = (items: WeatherIndeterminate[], fromDate: DateTime, toDate: DateTime) => {
  const dateInterval = createDateInterval(fromDate, toDate)
  const groupedByStationCode = groupby(items, 'station_code')
  const allActuals: WeatherIndeterminate[] = [...items]
  for (const values of Object.values(groupedByStationCode)) {
    const stationCode = values[0].station_code
    const stationName = values[0].station_name
    // We expect one actual per date in our date interval
    if (values.length < dateInterval.length) {
      for (const date of dateInterval) {
        if (!values.some(value => value.utc_timestamp === date)) {
          const missingActual = createEmptyWeatherIndeterminate(
            stationCode,
            stationName,
            date,
            WeatherDeterminate.ACTUAL
          )
          allActuals.push(missingActual)
        }
      }
    }
  }
  return allActuals
}

/**
 * Given an array of WeatherIndeterminates and a date range, ensure a WeatherIndeterminate is present for each
 * day for each station code. Used for creating empty Actual and Forecast WeatherIndeterminates.
 * @param items An array of WeatherIndeterminates that may need additional empty values added.
 * @param fromDate The start date for which values are required (inclusive).
 * @param toDate The end date for which values are required (inclusive).
 * @returns An array of WeatherIndeterminates with all required values present. Values may
 * contain NaN for dates in the future or dates where the backend does not provide data.
 */
const fillMissingForecasts = (
  items: WeatherIndeterminate[],
  fromDate: DateTime,
  toDate: DateTime,
  stationCodes: number[]
) => {
  const dateInterval = createDateInterval(fromDate, toDate)
  const groupedByStationCode = groupby(items, 'station_code')
  for (const stationCode of stationCodes) {
    if (isUndefined(groupedByStationCode[stationCode])) {
      groupedByStationCode[stationCode] = []
    }
  }
  const allWeatherIndeterminates: WeatherIndeterminate[] = [...items]
  for (const [key, values] of Object.entries(groupedByStationCode)) {
    const stationCode = key
    const stationName = ''
    // We expect one WeatherIndetermiante per date in our date interval
    if (values.length < dateInterval.length) {
      for (const date of dateInterval) {
        if (!values.some(value => value.utc_timestamp === date)) {
          const missing = createEmptyWeatherIndeterminate(
            parseInt(stationCode),
            stationName,
            date,
            WeatherDeterminate.FORECAST
          )
          allWeatherIndeterminates.push(missing)
        }
      }
    }
  }
  return allWeatherIndeterminates
}

/**
 * Given an array of WeatherIndeterminates and a date range, ensure predictions are present for each
 * day for each station code for each weather model.
 * @param items An array of WeatherIndeterminates that may need additional empty predictions added.
 * @param fromDate The start date for which predictions are required (inclusive).
 * @param toDate The end date for which predictions are required (inclusive).
 * @returns An array of WeatherIndeterminates with all required predictions are present. Predictions
 * may contain NaN values for dates in the future or dates where the backend does not provide data.
 */
const fillMissingPredictions = (items: WeatherIndeterminate[], fromDate: DateTime, toDate: DateTime) => {
  const modelDeterminates: WeatherDeterminateType[] = [
    WeatherDeterminate.GDPS,
    WeatherDeterminate.GFS,
    WeatherDeterminate.HRDPS,
    WeatherDeterminate.RDPS
  ]
  const dateInterval = createDateInterval(fromDate, toDate)
  const groupedByStationCode = groupby(items, 'station_code')
  const allPredictions = [...items]
  for (const values of Object.values(groupedByStationCode)) {
    const stationCode = values[0].station_code
    const stationName = values[0].station_name
    const groupedByUtcTimestamp = groupby(values, 'utc_timestamp')
    for (const [key, values2] of Object.entries(groupedByUtcTimestamp)) {
      for (const determinate of modelDeterminates) {
        const hasDeterminate = values2.filter(value => value.determinate === determinate)
        if (hasDeterminate.length === 0) {
          const missingDeterminate = createEmptyWeatherIndeterminate(stationCode, stationName, key, determinate)
          allPredictions.push(missingDeterminate)
        }
      }
    }
    const utcTimestampKeys = Object.keys(groupedByUtcTimestamp)
    for (const date of dateInterval) {
      if (utcTimestampKeys.indexOf(date) === -1) {
        for (const determinate of modelDeterminates) {
          const missingDeterminate = createEmptyWeatherIndeterminate(stationCode, stationName, date, determinate)
          allPredictions.push(missingDeterminate)
        }
      }
    }
  }
  return allPredictions
}

/**
 *
 * @param state Selector for all WeatherIndeterminates. Necessary for optimization/caching and is used
 * by the selectAllMoreCast2Rows selector.
 * @returns An array consisting of all WeatherInterminates.
 */
const selectWeatherIndeterminates = (state: RootState) => state.weatherIndeterminates

export const selectAllMoreCast2Rows = createSelector([selectWeatherIndeterminates], weatherIndeterminates => {
  // Since ids are a composite of a station code and date, grouping by id ensures that each group represents
  // the weather indeterminates for a single station and date
  const groupedById = groupby(
    [...weatherIndeterminates.actuals, ...weatherIndeterminates.forecasts, ...weatherIndeterminates.predictions],
    'id'
  )

  const rows: MoreCast2Row[] = []

  for (const values of Object.values(groupedById)) {
    if (!values.length) {
      return
    }
    const firstItem = values[0]
    const row = createEmptyMoreCast2Row(
      firstItem.id,
      firstItem.station_code,
      firstItem.station_name,
      DateTime.fromISO(firstItem.utc_timestamp)
    )

    for (const value of values) {
      switch (value.determinate) {
        case WeatherDeterminate.ACTUAL:
          row.precipActual = getNumberOrNaN(value.precipitation)
          row.rhActual = getNumberOrNaN(value.relative_humidity)
          row.tempActual = getNumberOrNaN(value.temperature)
          row.windDirectionActual = getNumberOrNaN(value.wind_direction)
          row.windSpeedActual = getNumberOrNaN(value.wind_speed)
          break
        case WeatherDeterminate.FORECAST:
          row.precipForecast = {
            choice: ModelChoice.FORECAST,
            value: getNumberOrNaN(value.precipitation)
          }
          row.rhForecast = {
            choice: ModelChoice.FORECAST,
            value: getNumberOrNaN(value.relative_humidity)
          }
          row.tempForecast = {
            choice: ModelChoice.FORECAST,
            value: getNumberOrNaN(value.temperature)
          }
          row.windDirectionForecast = {
            choice: ModelChoice.FORECAST,
            value: getNumberOrNaN(value.wind_direction)
          }
          row.windSpeedForecast = {
            choice: ModelChoice.FORECAST,
            value: getNumberOrNaN(value.wind_speed)
          }
          break
        case WeatherDeterminate.GDPS:
          row.precipGDPS = getNumberOrNaN(value.precipitation)
          row.rhGDPS = getNumberOrNaN(value.relative_humidity)
          row.tempGDPS = getNumberOrNaN(value.temperature)
          row.windDirectionGDPS = getNumberOrNaN(value.wind_direction)
          row.windSpeedGDPS = getNumberOrNaN(value.wind_speed)
          break
        case WeatherDeterminate.GFS:
          row.precipGFS = getNumberOrNaN(value.precipitation)
          row.rhGFS = getNumberOrNaN(value.relative_humidity)
          row.tempGFS = getNumberOrNaN(value.temperature)
          row.windDirectionGFS = getNumberOrNaN(value.wind_direction)
          row.windSpeedGFS = getNumberOrNaN(value.wind_speed)
          break
        case WeatherDeterminate.HRDPS:
          row.precipHRDPS = getNumberOrNaN(value.precipitation)
          row.rhHRDPS = getNumberOrNaN(value.relative_humidity)
          row.tempHRDPS = getNumberOrNaN(value.temperature)
          row.windDirectionHRDPS = getNumberOrNaN(value.wind_direction)
          row.windSpeedHRDPS = getNumberOrNaN(value.wind_speed)
          break
        case WeatherDeterminate.RDPS:
          row.precipRDPS = getNumberOrNaN(value.precipitation)
          row.rhRDPS = getNumberOrNaN(value.relative_humidity)
          row.tempRDPS = getNumberOrNaN(value.temperature)
          row.windDirectionRDPS = getNumberOrNaN(value.wind_direction)
          row.windSpeedRDPS = getNumberOrNaN(value.wind_speed)
          break
        default:
        // no-op
      }
    }
    rows.push(row as MoreCast2Row)
  }

  return rows
})

export const selectVisibleMoreCast2Rows = createSelector(
  [selectAllMoreCast2Rows, selectSelectedStations],
  (rows, selectedStations) => {
    let visibleRows: MoreCast2Row[] = []
    for (const station of selectedStations) {
      const filteredRows = rows?.filter(row => row.stationCode === station.station_code) || []
      visibleRows = [...visibleRows, ...filteredRows]
    }
    const sortedRows = sortRowsForDisplay(visibleRows)
    return sortedRows
  }
)

export const selectForecastMoreCast2Rows = createSelector([selectAllMoreCast2Rows], allMorecast2Rows =>
  allMorecast2Rows?.map(row => ({
    id: row.id,
    stationCode: row.stationCode,
    stationName: row.stationName,
    forDate: row.forDate,
    precip: row.precipForecast,
    rh: row.rhForecast,
    temp: row.tempForecast,
    windDirection: row.windDirectionForecast,
    windSpeed: row.windSpeedForecast
  }))
)

export const selectWeatherIndeterminatesLoading = (state: RootState) => state.weatherIndeterminates.loading

function sortRowsForDisplay(rows: MoreCast2Row[]) {
  const groupedRows = groupRowsByStationName(rows)
  const keys = Object.keys(groupedRows)
  keys.sort()
  let sortedRows: MoreCast2Row[] = []
  for (const key of keys) {
    const rowsForKey = groupedRows[key]
    sortedRows = [...sortedRows, ...rowsForKey]
  }
  return sortedRows
}

function groupRowsByStationName(rows: MoreCast2Row[]) {
  return rows.reduce((acc: { [key: string]: MoreCast2Row[] }, item: MoreCast2Row) => {
    const group = item.stationName
    acc[group] = acc[group] || []
    acc[group].push(item)

    return acc
  }, {})
}

/**
 *
 * @param value Given a number or null value, returns the number or NaN.
 * @returns A number or NaN.
 */
const getNumberOrNaN = (value: number | null) => {
  return value || NaN
}

/**
 * Creates an empty MoreCast2Row.
 * @param id The id of the row.
 * @param stationCode The station code.
 * @param stationName The station name.
 * @param forDate The date the row is for.
 * @returns
 */
const createEmptyMoreCast2Row = (
  id: string,
  stationCode: number,
  stationName: string,
  forDate: DateTime
): MoreCast2Row => {
  return {
    id,
    stationCode,
    stationName,
    forDate,
    precipActual: NaN,
    rhActual: NaN,
    tempActual: NaN,
    windDirectionActual: NaN,
    windSpeedActual: NaN,

    // GDPS model predictions
    precipGDPS: NaN,
    rhGDPS: NaN,
    tempGDPS: NaN,
    windDirectionGDPS: NaN,
    windSpeedGDPS: NaN,

    // GFS model predictions
    precipGFS: NaN,
    rhGFS: NaN,
    tempGFS: NaN,
    windDirectionGFS: NaN,
    windSpeedGFS: NaN,

    // HRDPS model predictions
    precipHRDPS: NaN,
    rhHRDPS: NaN,
    tempHRDPS: NaN,
    windDirectionHRDPS: NaN,
    windSpeedHRDPS: NaN,

    // RDPS model predictions
    precipRDPS: NaN,
    rhRDPS: NaN,
    tempRDPS: NaN,
    windDirectionRDPS: NaN,
    windSpeedRDPS: NaN
  }
}

/**
 * Creates a WeatherIndeterminate with NaN values for each weather parameter.
 * @param station_code The station code
 * @param station_name The station name.
 * @param utc_timestamp The date the WeatherIndeterminate is for.
 * @param determinate The Determinate type (eg. ACTUAL, HRDPS, GFS, etc...)
 * @returns A WeatherIndeterminate with NaN values for weather parameters.
 */
const createEmptyWeatherIndeterminate = (
  station_code: number,
  station_name: string,
  utc_timestamp: string,
  determinate: WeatherDeterminateType
) => {
  return {
    id: '',
    station_code,
    station_name,
    determinate,
    utc_timestamp,
    precipitation: null,
    relative_humidity: null,
    temperature: null,
    wind_direction: null,
    wind_speed: null
  }
}

/**
 * Groups the given WeatherIndeterminate array by the provided property.
 * @param items THe array to be grouped.
 * @param property The property to group on.
 * @returns An object with keys equivalent to the unqiue values of the provided property and arrays
 * of WeatherIndeterminates.
 */
const groupby = (items: WeatherIndeterminate[], property: keyof WeatherIndeterminate) => {
  return items.reduce((acc: { [key: string]: WeatherIndeterminate[] }, item: WeatherIndeterminate) => {
    const group = item[property] as string
    acc[group] = acc[group] || []
    acc[group].push(item)

    return acc
  }, {})
}
