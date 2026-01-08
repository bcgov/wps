import { createSelector, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { getAllRunDates, getMostRecentRunDate, getSFMSBounds, RunType, SFMSBounds } from 'api/fbaAPI'
import { AppThunk } from 'app/store'
import { DateTime } from 'luxon'
import { logError } from 'utils/error'

export interface RunDateState {
  loading: boolean
  error: string | null
  runDates: DateTime[]
  mostRecentRunDate: string | null
  sfmsBoundsError: string | null
  sfmsBounds: SFMSBounds | null
}

export const initialState: RunDateState = {
  loading: false,
  error: null,
  runDates: [],
  mostRecentRunDate: null,
  sfmsBoundsError: null,
  sfmsBounds: null
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
    getSFMSBoundsStart(state: RunDateState) {
      state.sfmsBounds = null
    },
    getSFMSBoundsFailed(state: RunDateState, action: PayloadAction<string>) {
      state.sfmsBounds = null
      state.sfmsBoundsError = action.payload
    },
    getSFMSBoundsSuccess(state: RunDateState, action: PayloadAction<{ sfms_bounds: SFMSBounds }>) {
      state.sfmsBoundsError = null
      state.sfmsBounds = action.payload.sfms_bounds
    }
  }
})

export const {
  getRunDatesStart,
  getRunDatesFailed,
  getRunDatesSuccess,
  getSFMSBoundsStart,
  getSFMSBoundsFailed,
  getSFMSBoundsSuccess
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

export const fetchSFMSBounds = (): AppThunk => async dispatch => {
  try {
    dispatch(getSFMSBoundsStart())
    const bounds = await getSFMSBounds()
    dispatch(getSFMSBoundsSuccess(bounds))
  } catch (err) {
    dispatch(getSFMSBoundsFailed((err as Error).toString()))
    logError(err)
  }
}

// Selectors
const selectSFMSBounds = (state: { runDates: RunDateState }) => state.runDates.sfmsBounds

const findBoundsInOrder = (
  sfmsBounds: SFMSBounds | null,
  sortFn: (a: string, b: string) => number,
  hasValue: (bounds: { minimum: string; maximum: string }) => boolean
) => {
  if (!sfmsBounds) return null

  const years = Object.keys(sfmsBounds).sort(sortFn)

  for (const year of years) {
    const bounds = sfmsBounds[year]?.forecast
    if (bounds && hasValue(bounds)) {
      return bounds
    }
  }
  return null
}

export const selectLatestSFMSBounds = createSelector([selectSFMSBounds], sfmsBounds =>
  findBoundsInOrder(sfmsBounds, (a, b) => b.localeCompare(a), bounds => !!bounds.maximum)
)

export const selectEarliestSFMSBounds = createSelector([selectSFMSBounds], sfmsBounds =>
  findBoundsInOrder(sfmsBounds, (a, b) => a.localeCompare(b), bounds => !!bounds.minimum)
)
