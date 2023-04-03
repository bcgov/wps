import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { getObservedDailies, ObservedAndYesterdayDailiesResponse, ObservedDaily } from 'api/moreCast2API'
import { AppThunk } from 'app/store'
import { buildYesterdayDailiesFromObserved, parseObservedDailiesFromResponse } from 'features/moreCast2/util'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  observedDailies: ObservedDaily[]
  yesterdayDailies: ObservedDaily[]
}

const initialState: State = {
  loading: false,
  error: null,
  observedDailies: [],
  yesterdayDailies: []
}

const observedDailiesSlice = createSlice({
  name: 'ObservedDailiesSlice',
  initialState,
  reducers: {
    getObservedDailiesStart(state: State) {
      state.error = null
      state.observedDailies = []
      state.yesterdayDailies = []
      state.loading = true
    },
    getObservedDailiesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getObservedDailiesSuccess(state: State, action: PayloadAction<ObservedAndYesterdayDailiesResponse>) {
      state.error = null
      state.observedDailies = action.payload.observedDailies
      state.yesterdayDailies = action.payload.yesterdayDailies
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
  (stationCodes: number[], fromDate: string, toDate: string): AppThunk =>
  async dispatch => {
    try {
      if (stationCodes.length) {
        dispatch(getModelStationPredictionsStart())
        const observedDailiesResponse = await getObservedDailies(stationCodes, fromDate)
        const observedDailies: ObservedDaily[] = parseObservedDailiesFromResponse(observedDailiesResponse)
        const yesterdayDailies = buildYesterdayDailiesFromObserved(observedDailies, toDate)
        dispatch(getObservedDailiesSuccess({ observedDailies: observedDailies, yesterdayDailies: yesterdayDailies }))
      }
    } catch (err) {
      dispatch(getObservedDailiesFailed((err as Error).toString()))
      logError(err)
    }
  }
