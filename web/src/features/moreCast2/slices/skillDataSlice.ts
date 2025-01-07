import { fetchSkillStats2, WeatherParamSkillData } from '@/api/skillAPI'
import { AppThunk } from '@/app/store'
import { selectSelectedStations } from '@/features/moreCast2/slices/selectedStationsSlice'
import { logError } from '@/utils/error'
import { createSelector, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { RootState } from 'app/rootReducer'
import { DateTime } from 'luxon'

export interface SkillDataState {
  error: string | null
  loading: boolean
  skillData: WeatherParamSkillData[]
}

export const initialState: SkillDataState = {
  error: null,
  loading: false,
  skillData: []
}

const skillDataSlice = createSlice({
  name: 'skillDataSlice',
  initialState,
  reducers: {
      getSkillDataStart(state: SkillDataState) {
        state.error = null
        state.loading = true
        state.skillData = []

      },
      getSkillDataFailed(state: SkillDataState, action: PayloadAction<string>) {
        state.error = action.payload
        state.loading = false
      },
      getSkillDataSuccess(state: SkillDataState, action: PayloadAction<WeatherParamSkillData[]>) {
        state.loading = false
        state.error = null
        state.skillData = action.payload
      }
    }
})

export const { getSkillDataStart, getSkillDataFailed, getSkillDataSuccess } = skillDataSlice.actions

export default skillDataSlice.reducer

export const selectSkillData = (state: RootState) => state.skillData.skillData

export const getSkillData = ( startDate: DateTime, days: number, stationCodes: number[]): AppThunk =>
  async dispatch => {
      try {
        dispatch(getSkillDataStart())
        const data = await fetchSkillStats2(startDate, days, stationCodes)
        dispatch(getSkillDataSuccess(data.skillData))
      } catch (err) {
        dispatch(getSkillDataFailed((err as Error).toString()))
        logError(err)
      }
  }
