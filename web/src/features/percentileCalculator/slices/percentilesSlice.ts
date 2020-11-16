import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { getPercentiles, PercentilesResponse, YearRange } from 'api/percentileAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface PercentilesState {
  loading: boolean
  error: string | null
  result: PercentilesResponse | null
}

export const percentileInitialState: PercentilesState = {
  loading: false,
  error: null,
  result: null
}

const percentiles = createSlice({
  name: 'percentile',
  initialState: percentileInitialState,
  reducers: {
    getPercentilesStart(state: PercentilesState) {
      state.loading = true
    },
    getPercentilesSuccess(
      state: PercentilesState,
      action: PayloadAction<PercentilesResponse>
    ) {
      state.result = action.payload
      state.loading = false
      state.error = null
    },
    getPercentilesFailed(state: PercentilesState, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    resetPercentilesResult(state: PercentilesState) {
      state.result = null
    }
  }
})

export const {
  getPercentilesStart,
  getPercentilesFailed,
  getPercentilesSuccess,
  resetPercentilesResult
} = percentiles.actions

export default percentiles.reducer

export const fetchPercentiles = (
  stationCodes: number[],
  percentile: number,
  yearRange: YearRange
): AppThunk => async dispatch => {
  try {
    dispatch(getPercentilesStart())
    const result = await getPercentiles(stationCodes, percentile, yearRange)
    dispatch(getPercentilesSuccess(result))
  } catch (err) {
    dispatch(getPercentilesFailed(err.toString()))
    logError(err)
  }
}
