import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { Forecast, getNoonForecasts, NoonForecastValue } from 'api/forecastAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  allNoonForecastsByStation: Record<number, NoonForecastValue[] | undefined>
  pastNoonForecastsByStation: Record<number, NoonForecastValue[] | undefined>
  noonForecastsByStation: Record<number, NoonForecastValue[] | undefined>
}

const initialState: State = {
  loading: false,
  error: null,
  allNoonForecastsByStation: {},
  pastNoonForecastsByStation: {},
  noonForecastsByStation: {}
}

const forecastsSlice = createSlice({
  name: 'forecasts',
  initialState,
  reducers: {
    getForecastsStart(state: State) {
      state.loading = true
      state.error = null
    },
    getForecastsFailed(state: State, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    getForecastsSuccess(state: State, action: PayloadAction<Forecast[]>) {
      action.payload.forEach(forecast => {
        const sCode = forecast.station_code
        if (sCode) {
          const allForecasts: NoonForecastValue[] = []

          const currDate = new Date()
          const pastForecasts: NoonForecastValue[] = []

          // only add the most recent forecast for the station and datetime
          // (query returns forecasts in order for each datetime, from most recently
          // issued down to first issued)
          let prevDatetime: string
          const mostRecentForecasts: NoonForecastValue[] = []
          forecast.values.forEach(value => {
            const isDiffDatetime = prevDatetime !== value.datetime
            if (isDiffDatetime) {
              const isFutureForecast = new Date(value.datetime) >= currDate
              if (isFutureForecast) {
                mostRecentForecasts.push(value)
              } else {
                pastForecasts.push(value)
              }

              allForecasts.push(value)
              prevDatetime = value.datetime
            }
          })
          state.allNoonForecastsByStation[sCode] = allForecasts
          state.pastNoonForecastsByStation[sCode] = pastForecasts
          state.noonForecastsByStation[sCode] = mostRecentForecasts
        }
      })
      state.loading = false
      state.error = null
    }
  }
})

export const {
  getForecastsStart,
  getForecastsFailed,
  getForecastsSuccess
} = forecastsSlice.actions

export default forecastsSlice.reducer

export const fetchForecasts = (
  stationCodes: number[],
  timeOfInterest: string
): AppThunk => async dispatch => {
  try {
    dispatch(getForecastsStart())
    const forecasts = await getNoonForecasts(stationCodes, timeOfInterest)
    dispatch(getForecastsSuccess(forecasts))
  } catch (err) {
    dispatch(getForecastsFailed(err.toString()))
    logError(err)
  }
}
