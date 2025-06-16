import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getAllRunDates, getMostRecentRunDate, getSFMSRunDateBounds, RunType, SFMSBounds } from 'api/fbaAPI'
import { DateTime } from 'luxon'

export interface RunDateState {
  loading: boolean
  error: string | null
  runDates: DateTime[]
  mostRecentRunDate: string | null
  sfmsBounds: SFMSBounds | null
  sfmsBoundsError: string | null
}

const initialState: RunDateState = {
  loading: false,
  error: null,
  runDates: [],
  mostRecentRunDate: null,
  sfmsBounds: null,
  sfmsBoundsError: null
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
    },
    getRunDateBoundsStart(state: RunDateState) {
      state.sfmsBounds = null
    },
    getRunDateBoundsFailed(state: RunDateState, action: PayloadAction<string>) {
      state.sfmsBounds = null
      state.sfmsBoundsError = action.payload
    },
    getRunDateBoundsSuccess(state: RunDateState, action: PayloadAction<{ sfms_bounds: SFMSBounds }>) {
      state.sfmsBoundsError = null
      state.sfmsBounds = action.payload.sfms_bounds
    }
  }
})

export const {
  getRunDatesStart,
  getRunDatesFailed,
  getRunDatesSuccess,
  getRunDateBoundsStart,
  getRunDateBoundsFailed,
  getRunDateBoundsSuccess
} = runDatesSlice.actions

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

export const fetchSFMSBounds =
  (runType: RunType, year: number): AppThunk =>
  async dispatch => {
    try {
      dispatch(getRunDateBoundsStart())
      const bounds = await getSFMSRunDateBounds(runType, year)
      dispatch(getRunDateBoundsSuccess(bounds))
    } catch (err) {
      dispatch(getRunDateBoundsFailed((err as Error).toString()))
      logError(err)
    }
  }
