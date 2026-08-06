import { createSelector, createSlice, type PayloadAction } from '@reduxjs/toolkit'
import { RunType } from '@wps/api/runType'
import { getSFMSInsightsBounds } from '@wps/api/sfmsAPI'
import type { SFMSBounds, SFMSBoundsResponse } from '@wps/api/sfmsBounds'
import { logError } from '@wps/utils/error'
import type { AppThunk } from 'app/store'

export interface SFMSInsightsState {
  sfmsBounds: SFMSBounds | null | undefined
  sfmsBoundsLoading: boolean
  sfmsBoundsError: string | null
}

export const initialState: SFMSInsightsState = {
  sfmsBounds: undefined,
  sfmsBoundsLoading: false,
  sfmsBoundsError: null
}

const sfmsInsightsSlice = createSlice({
  name: 'sfmsInsights',
  initialState,
  reducers: {
    getSFMSInsightsBoundsStart(state: SFMSInsightsState) {
      state.sfmsBounds = null
      state.sfmsBoundsLoading = true
      state.sfmsBoundsError = null
    },
    getSFMSInsightsBoundsFailed(state: SFMSInsightsState, action: PayloadAction<string>) {
      state.sfmsBounds = null
      state.sfmsBoundsLoading = false
      state.sfmsBoundsError = action.payload
    },
    getSFMSInsightsBoundsSuccess(state: SFMSInsightsState, action: PayloadAction<SFMSBoundsResponse>) {
      state.sfmsBounds = action.payload.sfms_bounds
      state.sfmsBoundsLoading = false
      state.sfmsBoundsError = null
    }
  }
})

export const { getSFMSInsightsBoundsStart, getSFMSInsightsBoundsFailed, getSFMSInsightsBoundsSuccess } =
  sfmsInsightsSlice.actions

export default sfmsInsightsSlice.reducer

export const fetchSFMSInsightsBounds = (): AppThunk => async dispatch => {
  try {
    dispatch(getSFMSInsightsBoundsStart())
    const bounds = await getSFMSInsightsBounds()
    dispatch(getSFMSInsightsBoundsSuccess(bounds))
  } catch (err) {
    dispatch(getSFMSInsightsBoundsFailed((err as Error).toString()))
    logError(err)
  }
}

type SFMSInsightsRootState = { sfmsInsights: SFMSInsightsState }

const selectSFMSInsights = (state: SFMSInsightsRootState) => state.sfmsInsights
const selectRunType = (_state: SFMSInsightsRootState, runType: RunType = RunType.ACTUAL) => runType

export const selectSFMSInsightsBounds = createSelector([selectSFMSInsights], sfmsInsights => sfmsInsights.sfmsBounds)

export const selectSFMSInsightsBoundsLoading = createSelector(
  [selectSFMSInsights],
  sfmsInsights => sfmsInsights.sfmsBoundsLoading
)

const getEarliestDate = (current: string, candidate: string) => {
  if (!candidate) return current
  if (!current || candidate < current) return candidate
  return current
}

const getLatestDate = (current: string, candidate: string) => {
  if (!candidate) return current
  if (!current || candidate > current) return candidate
  return current
}

export const selectCombinedSFMSInsightsBounds = createSelector([selectSFMSInsightsBounds], sfmsBounds => {
  if (!sfmsBounds) return null

  let minimum = ''
  let maximum = ''

  for (const yearBounds of Object.values(sfmsBounds)) {
    for (const sourceBounds of Object.values(yearBounds)) {
      minimum = getEarliestDate(minimum, sourceBounds.minimum)
      maximum = getLatestDate(maximum, sourceBounds.maximum)
    }
  }

  return minimum || maximum ? { minimum, maximum } : null
})

const findBoundsInOrder = (
  sfmsBounds: SFMSBounds | null | undefined,
  runType: RunType,
  sortFn: (a: string, b: string) => number,
  hasValue: (bounds: { minimum: string; maximum: string }) => boolean
) => {
  if (!sfmsBounds) return null

  for (const year of Object.keys(sfmsBounds).sort(sortFn)) {
    const bounds = sfmsBounds[year]?.[runType]
    if (bounds && hasValue(bounds)) {
      return bounds
    }
  }
  return null
}

export const selectLatestSFMSInsightsBounds = createSelector(
  [selectSFMSInsightsBounds, selectRunType],
  (sfmsBounds, runType) =>
    findBoundsInOrder(
      sfmsBounds,
      runType,
      (a, b) => b.localeCompare(a),
      bounds => !!bounds.maximum
    )
)

export const selectEarliestSFMSInsightsBounds = createSelector(
  [selectSFMSInsightsBounds, selectRunType],
  (sfmsBounds, runType) =>
    findBoundsInOrder(
      sfmsBounds,
      runType,
      (a, b) => a.localeCompare(b),
      bounds => !!bounds.minimum
    )
)
