import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getAllRunDates, getMostRecentRunDate } from 'api/fbaAPI'
import { DateTime } from 'luxon'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'

export interface RunDateState {
  loading: boolean
  error: string | null
  runDates: DateTime[]
  mostRecentRunDate: string | null
}

const initialState: RunDateState = {
  loading: false,
  error: null,
  runDates: [],
  mostRecentRunDate: null
}

const runDatesSlice = createSlice({
  name: 'runDates',
  initialState,
  reducers: {
    getRunDatesStart(state: RunDateState) {
      state.error = null
      state.loading = true
      state.runDates = []
      state.mostRecentRunDate = null
    },
    getRunDatesFailed(state: RunDateState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getRunDatesSuccess(
      state: RunDateState,
      action: PayloadAction<{ runDates: DateTime[]; mostRecentRunDate: string }>
    ) {
      state.error = null
      state.runDates = action.payload.runDates
      state.mostRecentRunDate = action.payload.mostRecentRunDate
      state.loading = false
    }
  }
})

export const { getRunDatesStart, getRunDatesFailed, getRunDatesSuccess } = runDatesSlice.actions

export default runDatesSlice.reducer

export const fetchSFMSRunDates =
  (runType: RunType, forDate: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(getRunDatesStart())
      const runDates = await getAllRunDates(runType, forDate)
      const mostRecentRunDate = await getMostRecentRunDate(runType, forDate)
      dispatch(getRunDatesSuccess({ runDates: runDates, mostRecentRunDate: mostRecentRunDate }))
    } catch (err) {
      dispatch(getRunDatesFailed((err as Error).toString()))
      logError(err)
    }
  }
