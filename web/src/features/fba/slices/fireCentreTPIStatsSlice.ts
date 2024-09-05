import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FireZoneTPIStats, getFireCentreTPIStats } from 'api/fbaAPI'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'

interface State {
  loading: boolean
  error: string | null
  fireCentreTPIStats: Record<string, FireZoneTPIStats[]> | null
}

const initialState: State = {
  loading: false,
  error: null,
  fireCentreTPIStats: null
}

const fireCentreTPIStatsSlice = createSlice({
  name: 'fireCentreTPIStats',
  initialState,
  reducers: {
    getFireCentreTPIStatsStart(state: State) {
      state.error = null
      state.fireCentreTPIStats = null
      state.loading = true
    },
    getFireCentreTPIStatsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireCentreTPIStatsSuccess(state: State, action: PayloadAction<Record<string, FireZoneTPIStats[]>>) {
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
