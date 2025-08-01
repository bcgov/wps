import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FireCentreHFIStats, getFireCentreHFIStats, RunType } from 'api/fbaAPI'

export interface FireCentreHFIFuelStatsState {
  error: string | null
  fireCentreHFIFuelStats: FireCentreHFIStats
  loading: boolean
}

export const initialState: FireCentreHFIFuelStatsState = {
  error: null,
  fireCentreHFIFuelStats: {},
  loading: false
}

const fireCentreHFIFuelStatsSlice = createSlice({
  name: 'fireCentreHfiFuelStats',
  initialState,
  reducers: {
    getFireCentreHFIFuelStatsStart(state: FireCentreHFIFuelStatsState) {
      state.error = null
      state.fireCentreHFIFuelStats = {}
      state.loading = true
    },
    getFireCentreHFIFuelStatsFailed(state: FireCentreHFIFuelStatsState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireCentreHFIFuelStatsSuccess(state: FireCentreHFIFuelStatsState, action: PayloadAction<FireCentreHFIStats>) {
      state.error = null
      state.fireCentreHFIFuelStats = action.payload
      state.loading = false
    }
  }
})

export const { getFireCentreHFIFuelStatsStart, getFireCentreHFIFuelStatsFailed, getFireCentreHFIFuelStatsSuccess } =
  fireCentreHFIFuelStatsSlice.actions

export default fireCentreHFIFuelStatsSlice.reducer

export const fetchFireCentreHFIFuelStats =
  (fireCentre: string, runType: RunType, forDate: string, runDatetime: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(getFireCentreHFIFuelStatsStart())
      const data = await getFireCentreHFIStats(runType, forDate, runDatetime, fireCentre)
      dispatch(getFireCentreHFIFuelStatsSuccess(data))
    } catch (err) {
      dispatch(getFireCentreHFIFuelStatsFailed((err as Error).toString()))
      logError(err)
    }
  }
