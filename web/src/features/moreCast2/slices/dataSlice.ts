import { createSelector, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { RootState } from 'app/rootReducer'
import {
  fetchWeatherIndeterminates,
  ModelChoice,
  WeatherIndeterminate,
  WeatherIndeterminatePayload,
  WeatherDeterminate,
  WeatherDeterminateChoices,
  WeatherDeterminateType
} from 'api/moreCast2API'
import { AppThunk } from 'app/store'
import { createDateInterval, rowIDHasher } from 'features/moreCast2/util'
import { DateTime } from 'luxon'
import { logError } from 'utils/error'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { groupBy, isNumber, isUndefined } from 'lodash'
import { StationGroupMember } from 'api/stationAPI'

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
 * @param stations The list of stations to retreive data for.
 * @param fromDate The start date from which to retrieve data from (inclusive).
 * @param toDate The end date from which to retrieve data from (inclusive).
 * @returns An array or WeatherIndeterminates.
 */
export const getWeatherIndeterminates =
  (stations: StationGroupMember[], fromDate: DateTime, toDate: DateTime): AppThunk =>
  async dispatch => {
    try {
      dispatch(getWeatherIndeterminatesStart())
      const stationMap = new Map<number, string>()
      for (const station of stations) {
        stationMap.set(station.station_code, station.display_label)
      }
      const data = await fetchWeatherIndeterminates([...stationMap.keys()], fromDate, toDate)
      let actuals = fillMissingWeatherIndeterminates(
        data.actuals,
        fromDate,
        toDate,
        stationMap,
        WeatherDeterminate.ACTUAL
      )
      let forecasts = fillMissingWeatherIndeterminates(
        data.forecasts,
        fromDate,
        toDate,
        stationMap,
        WeatherDeterminate.NULL
      )
      let predictions = fillMissingPredictions(data.predictions, fromDate, toDate, stationMap)
      actuals = addUniqueIds(actuals)
      forecasts = addUniqueIds(forecasts)
      predictions = addUniqueIds(predictions)
      const payload = {
        actuals,
        forecasts,
        predictions
      }
      dispatch(getWeatherIndeterminatesSuccess(payload))
    } catch (err) {
      dispatch(getWeatherIndeterminatesFailed((err as Error).toString()))
      logError(err)
    }
  }

export const createMoreCast2Rows = (
  actuals: WeatherIndeterminate[],
  forecasts: WeatherIndeterminate[],
  predictions: WeatherIndeterminate[]
): MoreCast2Row[] => {
  // Since ids are a composite of a station code and date, grouping by id ensures that each group represents
  // the weather indeterminates for a single station and date
  const groupedById = groupBy([...actuals, ...forecasts, ...predictions], 'id')

  const rows: MoreCast2Row[] = []

  for (const values of Object.values(groupedById)) {
    if (!values.length) {
      return []
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
        case WeatherDeterminate.NULL:
          row.precipForecast = {
            choice: forecastOrNull(value.determinate),
            value: getNumberOrNaN(value.precipitation)
          }
          row.rhForecast = {
            choice: forecastOrNull(value.determinate),
            value: getNumberOrNaN(value.relative_humidity)
          }
          row.tempForecast = {
            choice: forecastOrNull(value.determinate),
            value: getNumberOrNaN(value.temperature)
          }
          row.windDirectionForecast = {
            choice: forecastOrNull(value.determinate),
            value: getNumberOrNaN(value.wind_direction)
          }
          row.windSpeedForecast = {
            choice: forecastOrNull(value.determinate),
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
        case WeatherDeterminate.GDPS_BIAS:
          row.precipGDPS_BIAS = getNumberOrNaN(value.precipitation)
          row.rhGDPS_BIAS = getNumberOrNaN(value.relative_humidity)
          row.tempGDPS_BIAS = getNumberOrNaN(value.temperature)
          row.windDirectionGDPS_BIAS = getNumberOrNaN(value.wind_direction)
          row.windSpeedGDPS_BIAS = getNumberOrNaN(value.wind_speed)
          break
        case WeatherDeterminate.GFS:
          row.precipGFS = getNumberOrNaN(value.precipitation)
          row.rhGFS = getNumberOrNaN(value.relative_humidity)
          row.tempGFS = getNumberOrNaN(value.temperature)
          row.windDirectionGFS = getNumberOrNaN(value.wind_direction)
          row.windSpeedGFS = getNumberOrNaN(value.wind_speed)
          break
        case WeatherDeterminate.GFS_BIAS:
          row.precipGFS_BIAS = getNumberOrNaN(value.precipitation)
          row.rhGFS_BIAS = getNumberOrNaN(value.relative_humidity)
          row.tempGFS_BIAS = getNumberOrNaN(value.temperature)
          row.windDirectionGFS_BIAS = getNumberOrNaN(value.wind_direction)
          row.windSpeedGFS_BIAS = getNumberOrNaN(value.wind_speed)
          break
        case WeatherDeterminate.HRDPS:
          row.precipHRDPS = getNumberOrNaN(value.precipitation)
          row.rhHRDPS = getNumberOrNaN(value.relative_humidity)
          row.tempHRDPS = getNumberOrNaN(value.temperature)
          row.windDirectionHRDPS = getNumberOrNaN(value.wind_direction)
          row.windSpeedHRDPS = getNumberOrNaN(value.wind_speed)
          break
        case WeatherDeterminate.HRDPS_BIAS:
          row.precipHRDPS_BIAS = getNumberOrNaN(value.precipitation)
          row.rhHRDPS_BIAS = getNumberOrNaN(value.relative_humidity)
          row.tempHRDPS_BIAS = getNumberOrNaN(value.temperature)
          row.windDirectionHRDPS_BIAS = getNumberOrNaN(value.wind_direction)
          row.windSpeedHRDPS_BIAS = getNumberOrNaN(value.wind_speed)
          break
        case WeatherDeterminate.NAM:
          row.precipNAM = getNumberOrNaN(value.precipitation)
          row.rhNAM = getNumberOrNaN(value.relative_humidity)
          row.tempNAM = getNumberOrNaN(value.temperature)
          row.windDirectionNAM = getNumberOrNaN(value.wind_direction)
          row.windSpeedNAM = getNumberOrNaN(value.wind_speed)
          break
        case WeatherDeterminate.NAM_BIAS:
          row.precipNAM_BIAS = getNumberOrNaN(value.precipitation)
          row.rhNAM_BIAS = getNumberOrNaN(value.relative_humidity)
          row.tempNAM_BIAS = getNumberOrNaN(value.temperature)
          row.windDirectionNAM_BIAS = getNumberOrNaN(value.wind_direction)
          row.windSpeedNAM_BIAS = getNumberOrNaN(value.wind_speed)
          break
        case WeatherDeterminate.RDPS:
          row.precipRDPS = getNumberOrNaN(value.precipitation)
          row.rhRDPS = getNumberOrNaN(value.relative_humidity)
          row.tempRDPS = getNumberOrNaN(value.temperature)
          row.windDirectionRDPS = getNumberOrNaN(value.wind_direction)
          row.windSpeedRDPS = getNumberOrNaN(value.wind_speed)
          break
        case WeatherDeterminate.RDPS_BIAS:
          row.precipRDPS_BIAS = getNumberOrNaN(value.precipitation)
          row.rhRDPS_BIAS = getNumberOrNaN(value.relative_humidity)
          row.tempRDPS_BIAS = getNumberOrNaN(value.temperature)
          row.windDirectionRDPS_BIAS = getNumberOrNaN(value.wind_direction)
          row.windSpeedRDPS_BIAS = getNumberOrNaN(value.wind_speed)
          break
        default:
        // no-op
      }
    }
    rows.push(row)
  }

  return rows
}

const forecastOrNull = (determinate: WeatherDeterminateType): ModelChoice.FORECAST | ModelChoice.NULL => {
  return determinate === WeatherDeterminate.FORECAST ? ModelChoice.FORECAST : ModelChoice.NULL
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
 * Given an array of WeatherIndeterminates, a date range, a map of station codes to stations names and
 * a WeatherDeterminate, ensure a WeatherIndetermiante is present for each day for each station.
 * @param items An array of WeatherIndeterminates that may need additional empty actuals added.
 * @param fromDate The start date for which actuals are required (inclusive).
 * @param toDate The end date for which actuals are required (inclusive).
 * @param stationMap A mapping of station codes to station names.
 * @param determinate The type of WeatherDetermiante.
 * @returns An array of WeatherIndeterminates with all required actuals are present. Actuals may
 * contain NaN values for dates in the future or dates where the backend does not provide data.
 */
export const fillMissingWeatherIndeterminates = (
  items: WeatherIndeterminate[],
  fromDate: DateTime,
  toDate: DateTime,
  stationMap: Map<number, string>,
  determinate: WeatherDeterminateType
) => {
  const dateInterval = createDateInterval(fromDate, toDate)
  const groupedByStationCode = groupBy(items, 'station_code')
  for (const key of stationMap.keys()) {
    if (isUndefined(groupedByStationCode[key])) {
      groupedByStationCode[key] = []
    }
  }
  const weatherIndeterminates: WeatherIndeterminate[] = [...items]
  for (const [key, values] of Object.entries(groupedByStationCode)) {
    const stationCode = parseInt(key)
    const stationName = stationMap.get(stationCode) || ''
    // We expect one actual per date in our date interval
    if (values.length < dateInterval.length) {
      for (const date of dateInterval) {
        if (!values.some(value => value.utc_timestamp === date)) {
          const missing = createEmptyWeatherIndeterminate(stationCode, stationName, date, determinate)
          weatherIndeterminates.push(missing)
        }
      }
    }
  }
  return weatherIndeterminates
}

/**
 * Given an array of WeatherIndeterminates and a date range, ensure predictions are present for each
 * day for each station for each weather model.
 * @param items An array of WeatherIndeterminates that may need additional empty predictions added.
 * @param fromDate The start date for which predictions are required (inclusive).
 * @param toDate The end date for which predictions are required (inclusive).
 * @param stationMap A mapping of station codes to station names.
 * @returns An array of WeatherIndeterminates with all required predictions are present. Predictions
 * may contain NaN values for dates in the future or dates where the backend does not provide data.
 */
export const fillMissingPredictions = (
  items: WeatherIndeterminate[],
  fromDate: DateTime,
  toDate: DateTime,
  stationMap: Map<number, string>
) => {
  // This function is only concerned with weather models, so filter out non-weather model determinates
  const modelDeterminates: WeatherDeterminateType[] = WeatherDeterminateChoices.filter(
    determinate =>
      determinate !== WeatherDeterminate.ACTUAL &&
      determinate !== WeatherDeterminate.FORECAST &&
      determinate !== WeatherDeterminate.NULL
  )
  const dateInterval = createDateInterval(fromDate, toDate)
  const groupedByStationCode = createStationCodeToWeatherIndeterminateGroups(items, stationMap)

  const allPredictions = [...items]
  for (const [stationCodeAsString, weatherIndeterminatesByStationCode] of Object.entries(groupedByStationCode)) {
    const stationCode = parseInt(stationCodeAsString)
    const stationName = stationMap.get(stationCode) || ''
    const groupedByUtcTimestamp = createUtcTimeStampToWeatherIndeterminateGroups(
      weatherIndeterminatesByStationCode,
      dateInterval
    )

    for (const [utcTimestamp, weatherIndeterminatesByUtcTimestamp] of Object.entries(groupedByUtcTimestamp)) {
      for (const determinate of modelDeterminates) {
        const hasDeterminate = weatherIndeterminatesByUtcTimestamp.filter(value => value.determinate === determinate)
        if (hasDeterminate.length === 0) {
          const missingDeterminate = createEmptyWeatherIndeterminate(
            stationCode,
            stationName,
            utcTimestamp,
            determinate
          )
          allPredictions.push(missingDeterminate)
        }
      }
    }
  }
  return allPredictions
}

const createStationCodeToWeatherIndeterminateGroups = (
  items: WeatherIndeterminate[],
  stationMap: Map<number, string>
) => {
  const grouped = groupBy(items, 'station_code')
  for (const key of stationMap.keys()) {
    if (isUndefined(grouped[key])) {
      grouped[key] = []
    }
  }
  return grouped
}

const createUtcTimeStampToWeatherIndeterminateGroups = (items: WeatherIndeterminate[], dateInterval: string[]) => {
  const grouped = groupBy(items, 'utc_timestamp')
  for (const date of dateInterval) {
    if (isUndefined(grouped[date])) {
      grouped[date] = []
    }
  }
  return grouped
}

/**
 *
 * @param state Selector for all WeatherIndeterminates. Necessary for optimization/caching and is used
 * by the selectAllMoreCast2Rows selector.
 * @returns An array consisting of all WeatherInterminates.
 */
const selectWeatherIndeterminates = (state: RootState) => state.weatherIndeterminates

export const selectAllMoreCast2Rows = createSelector([selectWeatherIndeterminates], weatherIndeterminates => {
  const rows = createMoreCast2Rows(
    weatherIndeterminates.actuals,
    weatherIndeterminates.forecasts,
    weatherIndeterminates.predictions
  )
  const sortedRows = sortRowsByStationName(rows)
  return sortedRows
})

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

function sortRowsByStationName(rows: MoreCast2Row[]) {
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
  return isNumber(value) ? value : NaN
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

    // GDPS_BIAS model predictions
    precipGDPS_BIAS: NaN,
    rhGDPS_BIAS: NaN,
    tempGDPS_BIAS: NaN,
    windDirectionGDPS_BIAS: NaN,
    windSpeedGDPS_BIAS: NaN,

    // GFS model predictions
    precipGFS: NaN,
    rhGFS: NaN,
    tempGFS: NaN,
    windDirectionGFS: NaN,
    windSpeedGFS: NaN,

    // GFS_BIAS model predictions
    precipGFS_BIAS: NaN,
    rhGFS_BIAS: NaN,
    tempGFS_BIAS: NaN,
    windDirectionGFS_BIAS: NaN,
    windSpeedGFS_BIAS: NaN,

    // HRDPS model predictions
    precipHRDPS: NaN,
    rhHRDPS: NaN,
    tempHRDPS: NaN,
    windDirectionHRDPS: NaN,
    windSpeedHRDPS: NaN,

    // HRDPS_BIAS model predictions
    precipHRDPS_BIAS: NaN,
    rhHRDPS_BIAS: NaN,
    tempHRDPS_BIAS: NaN,
    windDirectionHRDPS_BIAS: NaN,
    windSpeedHRDPS_BIAS: NaN,

    // NAM model predictions
    precipNAM: NaN,
    rhNAM: NaN,
    tempNAM: NaN,
    windDirectionNAM: NaN,
    windSpeedNAM: NaN,

    // NAM_BIAS model predictions
    precipNAM_BIAS: NaN,
    rhNAM_BIAS: NaN,
    tempNAM_BIAS: NaN,
    windDirectionNAM_BIAS: NaN,
    windSpeedNAM_BIAS: NaN,

    // RDPS model predictions
    precipRDPS: NaN,
    rhRDPS: NaN,
    tempRDPS: NaN,
    windDirectionRDPS: NaN,
    windSpeedRDPS: NaN,

    // RDPS_BIAS model predictions
    precipRDPS_BIAS: NaN,
    rhRDPS_BIAS: NaN,
    tempRDPS_BIAS: NaN,
    windDirectionRDPS_BIAS: NaN,
    windSpeedRDPS_BIAS: NaN
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
): WeatherIndeterminate => {
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
