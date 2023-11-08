import { createSelector, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { RootState } from 'app/rootReducer'
import {
  fetchWeatherIndeterminates,
  ModelChoice,
  WeatherIndeterminate,
  WeatherIndeterminatePayload,
  WeatherDeterminate,
  WeatherDeterminateChoices,
  WeatherDeterminateType,
  UpdatedWeatherIndeterminateResponse,
  fetchCalculatedIndices
} from 'api/moreCast2API'
import { AppThunk } from 'app/store'
import { createDateInterval, rowIDHasher } from 'features/moreCast2/util'
import { DateTime } from 'luxon'
import { logError } from 'utils/error'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { groupBy, isEqual, isNull, isNumber, isUndefined } from 'lodash'
import { StationGroupMember } from 'api/stationAPI'

interface State {
  loading: boolean
  error: string | null
  actuals: WeatherIndeterminate[]
  forecasts: WeatherIndeterminate[]
  predictions: WeatherIndeterminate[]
  userEditedRows: MoreCast2Row[]
}

export const initialState: State = {
  loading: false,
  error: null,
  actuals: [],
  forecasts: [],
  predictions: [],
  userEditedRows: []
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
      state.userEditedRows = []
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
    },
    simulateWeatherIndeterminatesSuccess(state: State, action: PayloadAction<UpdatedWeatherIndeterminateResponse>) {
      const updatedForecasts = addUniqueIds(action.payload.simulated_forecasts)

      state.forecasts = state.forecasts.map(forecast => {
        const updatedForecast = updatedForecasts.find(item => item.id === forecast.id)
        return updatedForecast ?? forecast
      })
    },
    simulateWeatherIndeterminatesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
    },
    storeUserEditedRows(state: State, action: PayloadAction<MoreCast2Row[]>) {
      const storedRows = [...state.userEditedRows]

      for (const row of action.payload) {
        const existingIndex = storedRows.findIndex(storedRow => storedRow.id === row.id)
        if (existingIndex !== -1) {
          storedRows[existingIndex] = row
        } else {
          storedRows.push(row)
        }
      }
      state.userEditedRows = storedRows
    }
  }
})

export const {
  getWeatherIndeterminatesStart,
  getWeatherIndeterminatesFailed,
  getWeatherIndeterminatesSuccess,
  simulateWeatherIndeterminatesSuccess,
  simulateWeatherIndeterminatesFailed,
  storeUserEditedRows
} = dataSlice.actions

export default dataSlice.reducer

/**
 * Use the morecast2API to get WeatherIndeterminates from the backend. Fills in missing
 * actuals and predictions. Results are stored the Redux store.
 * @param stations The list of stations to retreive data for.
 * @param fromDate The start date from which to retrieve data from (inclusive).
 * @param toDate The end date from which to retrieve data from (inclusive).
 * @returns An array of WeatherIndeterminates.
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

/**
 * Use the morecast2API to get simulated Fire Weather Index value from the backend.
 * Results are stored in the Redux store.
 * @param rowsForSimulation List of MoreCast2Row's to simulate. The first row in the array must contain
 * valid values for all Fire Weather Indices.
 * @returns Array of MoreCast2Rows
 */
export const getSimulatedIndices =
  (rowsForSimulation: MoreCast2Row[]): AppThunk =>
  async dispatch => {
    try {
      const simulatedForecasts = await fetchCalculatedIndices(rowsForSimulation)
      dispatch(simulateWeatherIndeterminatesSuccess(simulatedForecasts))
    } catch (err) {
      dispatch(simulateWeatherIndeterminatesFailed((err as Error).toString()))
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
      DateTime.fromISO(firstItem.utc_timestamp),
      firstItem.latitude,
      firstItem.longitude
    )

    for (const value of values) {
      switch (value.determinate) {
        case WeatherDeterminate.ACTUAL:
          row.precipActual = getNumberOrNaN(value.precipitation)
          row.rhActual = getNumberOrNaN(value.relative_humidity)
          row.tempActual = getNumberOrNaN(value.temperature)
          row.windDirectionActual = getNumberOrNaN(value.wind_direction)
          row.windSpeedActual = getNumberOrNaN(value.wind_speed)
          row.ffmcCalcActual = getNumberOrNaN(value.fine_fuel_moisture_code)
          row.dmcCalcActual = getNumberOrNaN(value.duff_moisture_code)
          row.dcCalcActual = getNumberOrNaN(value.drought_code)
          row.isiCalcActual = getNumberOrNaN(value.initial_spread_index)
          row.buiCalcActual = getNumberOrNaN(value.build_up_index)
          row.fwiCalcActual = getNumberOrNaN(value.fire_weather_index)
          row.dgrCalcActual = getNumberOrNaN(value.danger_rating)
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
          row.ffmcCalcForecast = {
            choice: forecastOrNull(ModelChoice.NULL),
            value: getNumberOrNaN(value.fine_fuel_moisture_code)
          }
          row.dmcCalcForecast = {
            choice: forecastOrNull(ModelChoice.NULL),
            value: getNumberOrNaN(value.duff_moisture_code)
          }
          row.dcCalcForecast = {
            choice: forecastOrNull(ModelChoice.NULL),
            value: getNumberOrNaN(value.drought_code)
          }
          row.isiCalcForecast = {
            choice: forecastOrNull(ModelChoice.NULL),
            value: getNumberOrNaN(value.initial_spread_index)
          }
          row.buiCalcForecast = {
            choice: forecastOrNull(ModelChoice.NULL),
            value: getNumberOrNaN(value.build_up_index)
          }
          row.fwiCalcForecast = {
            choice: forecastOrNull(ModelChoice.NULL),
            value: getNumberOrNaN(value.fire_weather_index)
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

  // Set the forecasted precip value to 0 for rows which have no actual or forecasted precip value.
  for (const row of rows) {
    if (
      isNaN(row.precipActual) &&
      row.precipForecast &&
      row.precipForecast.choice === ModelChoice.NULL &&
      isNaN(row.precipForecast.value)
    ) {
      row.precipForecast.value = 0
    }
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
export const addUniqueIds = (items: WeatherIndeterminate[]) => {
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
    const stationName = stationMap.get(stationCode) ?? ''
    const latitude = values[0]?.latitude ?? 0
    const longitude = values[0]?.longitude ?? 0
    // We expect one actual per date in our date interval
    if (values.length < dateInterval.length) {
      for (const date of dateInterval) {
        if (!values.some(value => isEqual(DateTime.fromISO(value.utc_timestamp), DateTime.fromISO(date)))) {
          const missing = createEmptyWeatherIndeterminate(
            stationCode,
            stationName,
            date,
            determinate,
            latitude,
            longitude
          )
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
    const stationName = stationMap.get(stationCode) ?? ''
    const latitude = weatherIndeterminatesByStationCode[0]?.latitude ?? 0
    const longitude = weatherIndeterminatesByStationCode[0]?.longitude ?? 0
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
            determinate,
            latitude,
            longitude
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
  const grouped = groupBy(items, item => DateTime.fromISO(item.utc_timestamp).toISODate())
  for (const date of dateInterval) {
    const isoDate = DateTime.fromISO(date).toISODate()
    if (isNull(isoDate) || isUndefined(grouped[isoDate])) {
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
  const sortedRows = sortRowsByStationNameAndDate(rows)
  return sortedRows
})

export const selectUserEditedRows = createSelector([selectWeatherIndeterminates], weatherIndeterminates => {
  const rows = weatherIndeterminates.userEditedRows
  return rows
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

// Comparator function for use in sorting Luxon DateTime objects with JavaScript Array.prototype.sort
function compareDateTime(a: DateTime, b: DateTime) {
  if (a < b) {
    return -1
  } else if (a > b) {
    return 1
  } else {
    return 0
  }
}

function sortRowsByStationNameAndDate(rows: MoreCast2Row[]) {
  // Group the rows by station name to start
  const groupedRows = groupBy(rows, 'stationName')
  // Now sort the rows by 'forDate' within each group
  const groupedSorted: { [key: string]: MoreCast2Row[] } = {}
  for (const [key, value] of Object.entries(groupedRows)) {
    groupedSorted[key] = value.sort((a, b) => compareDateTime(a.forDate, b.forDate))
  }

  // Finally, sort the keys of the groups alphabetically and then build up a new
  // array of rows which will be sorted first by station name and then by the forDate
  const keys = Object.keys(groupedSorted)
  keys.sort()
  let sortedRows: MoreCast2Row[] = []
  for (const key of keys) {
    const rowsForKey = groupedSorted[key]
    sortedRows = [...sortedRows, ...rowsForKey]
  }
  return sortedRows
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
export const createEmptyMoreCast2Row = (
  id: string,
  stationCode: number,
  stationName: string,
  forDate: DateTime,
  latitude: number,
  longitude: number
): MoreCast2Row => {
  return {
    id,
    stationCode,
    stationName,
    forDate,
    latitude,
    longitude,
    precipActual: NaN,
    rhActual: NaN,
    tempActual: NaN,
    windDirectionActual: NaN,
    windSpeedActual: NaN,

    // Indices
    ffmcCalcActual: NaN,
    dmcCalcActual: NaN,
    dcCalcActual: NaN,
    isiCalcActual: NaN,
    buiCalcActual: NaN,
    fwiCalcActual: NaN,
    dgrCalcActual: NaN,

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
  determinate: WeatherDeterminateType,
  latitude: number,
  longitude: number
): WeatherIndeterminate => {
  return {
    id: '',
    station_code,
    station_name,
    latitude,
    longitude,
    determinate,
    utc_timestamp,
    precipitation: null,
    relative_humidity: null,
    temperature: null,
    wind_direction: null,
    wind_speed: null,
    fine_fuel_moisture_code: null,
    duff_moisture_code: null,
    drought_code: null,
    initial_spread_index: null,
    build_up_index: null,
    fire_weather_index: null,
    danger_rating: null
  }
}
