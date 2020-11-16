import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import {
  ForecastSummary,
  ForecastSummariesForStation,
  getForecastSummaries
} from 'api/forecastAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  forecastSummariesByStation: Record<number, ForecastSummary[] | undefined>
}

const initialState: State = {
  loading: false,
  error: null,
  forecastSummariesByStation: {}
}

const forecastSummariesSlice = createSlice({
  name: 'forecastSummaries',
  initialState,
  reducers: {
    getForecastSummariesStart(state: State) {
      state.error = null
      state.loading = true
    },
    getForecastSummariesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getForecastSummariesSuccess(
      state: State,
      action: PayloadAction<ForecastSummariesForStation[]>
    ) {
      state.error = null
      action.payload.forEach(summary => {
        if (summary.station) {
          const code = summary.station.code
          state.forecastSummariesByStation[code] = summary.values
        }
      })
      state.loading = false
    }
  }
})

export const {
  getForecastSummariesStart,
  getForecastSummariesFailed,
  getForecastSummariesSuccess
} = forecastSummariesSlice.actions

export default forecastSummariesSlice.reducer

export const fetchForecastSummaries = (
  stationCodes: number[]
): AppThunk => async dispatch => {
  try {
    dispatch(getForecastSummariesStart())
    const forecastSummaries = await getForecastSummaries(stationCodes)
    dispatch(getForecastSummariesSuccess(forecastSummaries))
  } catch (err) {
    dispatch(getForecastSummariesFailed(err.toString()))
    logError(err)
  }
}
