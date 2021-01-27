import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { PeakValuesResponse, getPeakValues } from 'api/peakBurninessAPI'

interface State {
  loading: boolean
  error: string | null
  peakBurninessValues: PeakValuesResponse | undefined
}

const initialState: State = {
  loading: false,
  error: null,
  peakBurninessValues: undefined
}

const peakBurninessSlice = createSlice({
  name: 'peak-burniness-slice',
  initialState: initialState,
  reducers: {
    getPeakValuesStart(state: State) {
      state.loading = true
    },
    getPeakValuesSuccess(state: State, action: PayloadAction<PeakValuesResponse>) {
      state.peakBurninessValues = action.payload
      state.loading = false
      state.error = null
    },
    getPeakValuesFailed(state: State, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    resetPeakValuesResult(state: State) {
      state.peakBurninessValues = undefined
    }
  }
})

export const {
  getPeakValuesFailed,
  getPeakValuesStart,
  getPeakValuesSuccess,
  resetPeakValuesResult
} = peakBurninessSlice.actions

export default peakBurninessSlice.reducer

export const fetchPeakValues = (stationCodes: number[]): AppThunk => async dispatch => {
  try {
    dispatch(getPeakValuesStart())
    const peakBurninessValues = await getPeakValues(stationCodes)
    dispatch(getPeakValuesSuccess(peakBurninessValues))
  } catch (err) {
    dispatch(getPeakValuesFailed(err.toString()))
    logError(err)
  }
}
