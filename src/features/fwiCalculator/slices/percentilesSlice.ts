import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import {
  getPercentiles,
  PercentilesResponse,
  YearRange
} from 'api/percentileAPI'
import { AppThunk } from 'app/store'

interface PercentilesState {
  isLoading: boolean
  error: string | null
  result: PercentilesResponse | null
}

export const percentileInitialState: PercentilesState = {
  isLoading: false,
  error: null,
  result: null
}

const percentiles = createSlice({
  name: 'percentile',
  initialState: percentileInitialState,
  reducers: {
    getPercentilesStart(state: PercentilesState) {
      state.isLoading = true
    },
    getPercentilesSuccess(
      state: PercentilesState,
      action: PayloadAction<PercentilesResponse>
    ) {
      state.result = action.payload
      state.isLoading = false
      state.error = null
    },
    getPercentilesFailed(
      state: PercentilesState,
      action: PayloadAction<string>
    ) {
      state.isLoading = false
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
  stations: number[],
  percentile: number,
  yearRange: YearRange
): AppThunk => async dispatch => {
  try {
    dispatch(getPercentilesStart())
    const result = await getPercentiles(stations, percentile, yearRange)
    dispatch(getPercentilesSuccess(result))
  } catch (err) {
    dispatch(getPercentilesFailed(err.toString()))
  }
}
