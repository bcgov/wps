import { createSelector, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { RootState } from 'app/rootReducer'
import {
  getWeatherIndeterminates,
  StationWeatherIndeterminate,
  StationWeatherIndeterminateResponse,
  WeatherDeterminate,
  WeatherDeterminateType
} from 'api/moreCast2API'
import { AppThunk } from 'app/store'
import { rowIDHasher } from 'features/moreCast2/util'
import { DateTime } from 'luxon'
import { logError } from 'utils/error'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { createDateInterval } from 'features/moreCast2/util'

interface State {
  loading: boolean
  error: string | null
  actuals: StationWeatherIndeterminate[]
  forecasts: StationWeatherIndeterminate[]
  predictions: StationWeatherIndeterminate[]
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
    getStationWeatherIndeterminatesStart(state: State) {
      state.error = null
      state.actuals = []
      state.forecasts = []
      state.predictions = []
      state.loading = true
    },
    getStationWeatherIndeterminatesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getStationWeatherIndeterminatesSuccess(state: State, action: PayloadAction<StationWeatherIndeterminateResponse>) {
      state.error = null
      state.actuals = action.payload.actuals
      state.forecasts = action.payload.forecasts
      state.predictions = action.payload.predictions
      state.loading = false
    }
  }
})

export const {
  getStationWeatherIndeterminatesStart,
  getStationWeatherIndeterminatesFailed,
  getStationWeatherIndeterminatesSuccess
} = dataSlice.actions

export default dataSlice.reducer

export const getStationWeatherIndeterminates =
  (stationCodes: number[], fromDate: DateTime, toDate: DateTime): AppThunk =>
  async dispatch => {
    try {
      dispatch(getStationWeatherIndeterminatesStart())
      const data = await getWeatherIndeterminates(stationCodes, fromDate, toDate)
      const actuals = fillMissingActuals(data.actuals, fromDate, toDate)
      const predictions = fillMissingPredictions(data.predictions, fromDate, toDate)
      data.actuals = addUniqueIds(actuals)
      data.predictions = addUniqueIds(predictions)
      data.forecasts = data.forecasts.map(item => ({
        ...item,
        id: rowIDHasher(item.station_code, DateTime.fromISO(item.utc_timestamp))
      }))
      dispatch(getStationWeatherIndeterminatesSuccess(data))
    } catch (err) {
      dispatch(getStationWeatherIndeterminatesFailed((err as Error).toString()))
      logError(err)
    }
  }

const addUniqueIds = (items: StationWeatherIndeterminate[]) => {
  return items.map(item => ({
    ...item,
    id: rowIDHasher(item.station_code, DateTime.fromISO(item.utc_timestamp))
  }))
}

const fillMissingPredictions = (items: StationWeatherIndeterminate[], fromDate: DateTime, toDate: DateTime) => {
  const modelDeterminates = [
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
          const missingDeterminate = createEmptyStationWeatherIndeterminate(stationCode, stationName, key, determinate)
          allPredictions.push(missingDeterminate)
        }
      }
    }
    const utcTimestampKeys = Object.keys(groupedByUtcTimestamp)
    for (const date of dateInterval) {
      if (utcTimestampKeys.indexOf(date) === -1) {
        for (const determinate of modelDeterminates) {
          const missingDeterminate = createEmptyStationWeatherIndeterminate(stationCode, stationName, date, determinate)
          allPredictions.push(missingDeterminate)
        }
      }
    }
  }
  return allPredictions
}

const fillMissingActuals = (items: StationWeatherIndeterminate[], fromDate: DateTime, toDate: DateTime) => {
  const dateInterval = createDateInterval(fromDate, toDate)
  const grouped = groupby(items, 'station_code')
  const allActuals = [...items]
  for (const values of Object.values(grouped)) {
    const stationCode = values[0].station_code
    const stationName = values[0].station_name
    // We expect one actual per date in our date interval
    if (values.length < dateInterval.length) {
      for (const date of dateInterval) {
        if (!values.some(value => value.utc_timestamp === date)) {
          const missingActual = createEmptyStationWeatherIndeterminate(
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

const selectWeatherIndeterminates = (state: RootState) => state.weatherIndeterminates

export const selectAllWeatherIndeterminates = (state: RootState) => {
  return [
    ...state.weatherIndeterminates.actuals,
    ...state.weatherIndeterminates.forecasts,
    ...state.weatherIndeterminates.predictions
  ]
}

const getNumberOrNaN = (value: number | null) => {
  return value || NaN
}

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
        // noop
      }
    }
    rows.push(row as MoreCast2Row)
  }

  return rows
})

// Commented out as selected stations are not actually set in the Redux store
// export const selectMoreCast2RowsFilteredByStationGroupsMembers = createSelector(
//   [selectMoreCast2Rows, selectSelectedStationGroupsMembers],
//   (rows, members) => {
//     if (isUndefined(rows) || isUndefined(members)) {
//       return []
//     }
//     let filteredRows: MoreCast2Row[] = []
//     const stationCodes = members.map(member => member.station_code)
//     for (const stationCode of stationCodes) {
//       const matchingRows = rows.filter(row => row.stationCode === stationCode)
//       filteredRows = [...filteredRows, ...matchingRows]
//     }
//     return filteredRows
//   }
// )

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

const createEmptyStationWeatherIndeterminate = (
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

const groupby = (items: StationWeatherIndeterminate[], property: keyof StationWeatherIndeterminate) => {
  return items.reduce((acc: { [key: string]: StationWeatherIndeterminate[] }, item: StationWeatherIndeterminate) => {
    const group = item[property] as string
    acc[group] = acc[group] || []
    acc[group].push(item)

    return acc
  }, {})
}
