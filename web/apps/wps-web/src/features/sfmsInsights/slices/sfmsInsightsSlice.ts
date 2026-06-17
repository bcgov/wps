import { createSelector, createSlice, type PayloadAction } from '@reduxjs/toolkit'
import { getSFMSInsightsBounds, type SFMSBounds, type SFMSBoundsResponse } from '@wps/api/sfmsAPI'
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

const selectSFMSInsights = (state: { sfmsInsights: SFMSInsightsState }) => state.sfmsInsights

export const selectSFMSInsightsBounds = createSelector([selectSFMSInsights], sfmsInsights => sfmsInsights.sfmsBounds)

export const selectSFMSInsightsBoundsLoading = createSelector(
  [selectSFMSInsights],
  sfmsInsights => sfmsInsights.sfmsBoundsLoading
)

const findActualBoundsInOrder = (
  sfmsBounds: SFMSBounds | null | undefined,
  sortFn: (a: string, b: string) => number,
  hasValue: (bounds: { minimum: string; maximum: string }) => boolean
) => {
  if (!sfmsBounds) return null

  for (const year of Object.keys(sfmsBounds).sort(sortFn)) {
    const bounds = sfmsBounds[year]?.actual
    if (bounds && hasValue(bounds)) {
      return bounds
    }
  }
  return null
}

export const selectLatestSFMSInsightsBounds = createSelector([selectSFMSInsightsBounds], sfmsBounds =>
  findActualBoundsInOrder(
    sfmsBounds,
    (a, b) => b.localeCompare(a),
    bounds => !!bounds.maximum
  )
)

export const selectEarliestSFMSInsightsBounds = createSelector([selectSFMSInsightsBounds], sfmsBounds =>
  findActualBoundsInOrder(
    sfmsBounds,
    (a, b) => a.localeCompare(b),
    bounds => !!bounds.minimum
  )
)
