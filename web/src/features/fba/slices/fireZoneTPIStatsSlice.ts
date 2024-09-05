import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FireZoneTPIStats, getFireZoneTPIStats } from 'api/fbaAPI'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'

interface State {
  loading: boolean
  error: string | null
  fireZoneTPIStats: FireZoneTPIStats | null
}

const initialState: State = {
  loading: false,
  error: null,
  fireZoneTPIStats: null
}

const fireZoneTPIStatsSlice = createSlice({
  name: 'fireZoneTPIStats',
  initialState,
  reducers: {
    getFireZoneTPIStatsStart(state: State) {
      state.error = null
      state.fireZoneTPIStats = null
      state.loading = true
    },
    getFireZoneTPIStatsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireZoneTPIStatsSuccess(state: State, action: PayloadAction<FireZoneTPIStats>) {
      state.error = null
      state.fireZoneTPIStats = action.payload
      state.loading = false
    }
  }
})

export const { getFireZoneTPIStatsStart, getFireZoneTPIStatsFailed, getFireZoneTPIStatsSuccess } =
fireZoneTPIStatsSlice.actions

export default fireZoneTPIStatsSlice.reducer

export const fetchFireZoneTPIStats =
  (fire_zone_id: number, runType: RunType, forDate: string, runDatetime: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(getFireZoneTPIStatsStart())
      const fireZoneTPIStats = await getFireZoneTPIStats(fire_zone_id, runType, forDate, runDatetime)
      dispatch(getFireZoneTPIStatsSuccess(fireZoneTPIStats))
    } catch (err) {
      dispatch(getFireZoneTPIStatsFailed((err as Error).toString()))
      logError(err)
    }
  }
