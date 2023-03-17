import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { MoreCast2ForecastRecord, getMoreCast2ForecastRecordsByDateRange } from 'api/moreCast2API'
import { AppThunk } from 'app/store'
import { rowIDHasher } from 'features/moreCast2/util'
import { DateTime } from 'luxon'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  forecasts: MoreCast2ForecastRecord[]
}

export const initialState: State = {
  loading: false,
  error: null,
  forecasts: []
}

const moreCast2ForecastsSlice = createSlice({
  name: 'MoreCast2ForecastsSlice',
  initialState,
  reducers: {
    getMoreCast2ForecastsStart(state: State) {
      state.error = null
      state.forecasts = []
      state.loading = true
    },
    getMoreCast2ForecastsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getMoreCast2ForecastsSuccess(state: State, action: PayloadAction<MoreCast2ForecastRecord[]>) {
      state.error = null
      state.forecasts = action.payload
      state.loading = false
    }
  }
})

export const { getMoreCast2ForecastsStart, getMoreCast2ForecastsFailed, getMoreCast2ForecastsSuccess } =
  moreCast2ForecastsSlice.actions

export default moreCast2ForecastsSlice.reducer

export const getMoreCast2Forecasts =
  (startDate: DateTime, endDate: DateTime, stationCodes: number[]): AppThunk =>
  async dispatch => {
    try {
      dispatch(getMoreCast2ForecastsStart())
      let forecasts: MoreCast2ForecastRecord[] = []
      if (stationCodes.length) {
        forecasts = (await getMoreCast2ForecastRecordsByDateRange(startDate, endDate, stationCodes)).map(forecast => ({
          ...forecast,
          id: rowIDHasher(forecast.station_code, DateTime.fromMillis(forecast.for_date))
        }))
      }
      dispatch(getMoreCast2ForecastsSuccess(forecasts))
    } catch (err) {
      dispatch(getMoreCast2ForecastsFailed((err as Error).toString()))
      logError(err)
    }
  }
