import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FireZoneStats, getZoneStats } from 'api/fbaAPI'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'

interface State {
  loading: boolean
  error: string | null
  fireZoneStats: Record<number, FireZoneStats[]>
}

const initialState: State = {
  loading: false,
  error: null,
  fireZoneStats: {}
}

const fireZoneStatsSlice = createSlice({
  name: 'fireZoneStats',
  initialState,
  reducers: {
    getFireZoneStatsStart(state: State) {
      state.error = null
      state.loading = true
    },
    getFireZoneStatsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireZoneStatsSuccess(state: State, action: PayloadAction<Record<number, FireZoneStats[]>>) {
      state.error = null
      state.fireZoneStats = action.payload
      state.loading = false
    }
  }
})

export const { getFireZoneStatsStart, getFireZoneStatsFailed, getFireZoneStatsSuccess } = fireZoneStatsSlice.actions

export default fireZoneStatsSlice.reducer

export const fetchZoneStats =
  (runType: RunType, forDate: string, runDatetime: string, zoneID: number): AppThunk =>
  async dispatch => {
    try {
      dispatch(getFireZoneStatsStart())
      const data = await getZoneStats(runType, forDate, runDatetime, zoneID)
      dispatch(getFireZoneStatsSuccess(data))
    } catch (err) {
      dispatch(getFireZoneStatsFailed((err as Error).toString()))
      logError(err)
    }
  }
