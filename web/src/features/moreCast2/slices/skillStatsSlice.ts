import { fetchSkillStats, WeatherParamSkillStats } from '@/api/skillAPI'
import { AppThunk } from '@/app/store'
import { logError } from '@/utils/error'
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { RootState } from 'app/rootReducer'
import { DateTime } from 'luxon'

export interface SkillStatsState {
  error: string | null
  loading: boolean
  skillStats: WeatherParamSkillStats[]
}

export const initialState: SkillStatsState = {
  error: null,
  loading: false,
  skillStats: []
}

const skillStatsSlice = createSlice({
  name: 'skillStatsSlice',
  initialState,
  reducers: {
      getSkillStatsStart(state: SkillStatsState) {
        state.error = null
        state.loading = true
        state.skillStats = []

      },
      getSkillStatsFailed(state: SkillStatsState, action: PayloadAction<string>) {
        state.error = action.payload
        state.loading = false
      },
      getSkillStatsSuccess(state: SkillStatsState, action: PayloadAction<WeatherParamSkillStats[]>) {
        state.loading = false
        state.error = null
        state.skillStats = action.payload
      }
    }
})

export const { getSkillStatsStart, getSkillStatsFailed, getSkillStatsSuccess } = skillStatsSlice.actions

export default skillStatsSlice.reducer

export const selectSkillStats = (state: RootState) => state.skillStats.skillStats

export const getSkillStats = ( startDate: DateTime, days: number, stationCodes: number[]): AppThunk =>
  async dispatch => {
      try {
        dispatch(getSkillStatsStart())
        const data = await fetchSkillStats(startDate, days, stationCodes)
        dispatch(getSkillStatsSuccess(data.skillStats))
      } catch (err) {
        dispatch(getSkillStatsFailed((err as Error).toString()))
        logError(err)
      }
  }
