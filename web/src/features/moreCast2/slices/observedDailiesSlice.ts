import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { getObservedDailies, ObservedDaily } from 'api/moreCast2API'
import { AppThunk } from 'app/store'
import { parseObservedDailiesFromResponse } from 'features/moreCast2/util'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  observedDailies: ObservedDaily[]
}

const initialState: State = {
  loading: false,
  error: null,
  observedDailies: []
}

const observedDailiesSlice = createSlice({
  name: 'ObservedDailiesSlice',
  initialState,
  reducers: {
    getObservedDailiesStart(state: State) {
      state.error = null
      state.observedDailies = []
      state.loading = true
    },
    getObservedDailiesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getObservedDailiesSuccess(state: State, action: PayloadAction<ObservedDaily[]>) {
      state.error = null
      state.observedDailies = action.payload
      state.loading = false
    }
  }
})

export const {
  getObservedDailiesStart: getModelStationPredictionsStart,
  getObservedDailiesFailed,
  getObservedDailiesSuccess
} = observedDailiesSlice.actions

export default observedDailiesSlice.reducer

export const getObservedStationDailies =
  (stationCodes: number[], fromDate: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(getModelStationPredictionsStart())
      if (stationCodes.length) {
        const observedDailiesResponse = await getObservedDailies(stationCodes, fromDate)
        const observedDailies: ObservedDaily[] = parseObservedDailiesFromResponse(observedDailiesResponse)
        dispatch(getObservedDailiesSuccess(observedDailies))
      }
    } catch (err) {
      dispatch(getObservedDailiesFailed((err as Error).toString()))
      logError(err)
    }
  }
