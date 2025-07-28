import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FireCentreTPIResponse, getFireCentreTPIStats, RunType } from 'api/fbaAPI'

export interface CentreTPIStatsState {
  error: string | null
  fireCentreTPIStats: FireCentreTPIResponse | null
  loading: boolean
}

export const initialState: CentreTPIStatsState = {
  error: null,
  fireCentreTPIStats: null,
  loading: false
}

const fireCentreTPIStatsSlice = createSlice({
  name: 'fireCentreTPIStats',
  initialState,
  reducers: {
    getFireCentreTPIStatsStart(state: CentreTPIStatsState) {
      state.error = null
      state.fireCentreTPIStats = null
      state.loading = true
    },
    getFireCentreTPIStatsFailed(state: CentreTPIStatsState, action: PayloadAction<string>) {
      state.error = action.payload
      state.fireCentreTPIStats = null
      state.loading = false
    },
    getFireCentreTPIStatsSuccess(state: CentreTPIStatsState, action: PayloadAction<FireCentreTPIResponse>) {
      state.error = null
      state.fireCentreTPIStats = action.payload
      state.loading = false
    }
  }
})

export const { getFireCentreTPIStatsStart, getFireCentreTPIStatsFailed, getFireCentreTPIStatsSuccess } =
  fireCentreTPIStatsSlice.actions

export default fireCentreTPIStatsSlice.reducer

export const fetchFireCentreTPIStats =
  (fireCentre: string, runType: RunType, forDate: string, runDatetime: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(getFireCentreTPIStatsStart())
      const fireCentreTPIStats = await getFireCentreTPIStats(fireCentre, runType, forDate, runDatetime)
      dispatch(getFireCentreTPIStatsSuccess(fireCentreTPIStats))
    } catch (err) {
      dispatch(getFireCentreTPIStatsFailed((err as Error).toString()))
      logError(err)
    }
  }
