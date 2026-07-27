import { createSelector, createSlice, type PayloadAction } from '@reduxjs/toolkit'
import { DateTime } from 'luxon'
import type { AppThunk, RootState } from '@/store'
import { ASA_GO_TIMEZONE } from '@/utils/constants'
import { getTodayKey } from '@/utils/dataSliceUtils'

export interface DateOfInterestState {
  dateKey: string
}

export const getInitialState = (): DateOfInterestState => ({
  dateKey: getTodayKey()
})

const dateOfInterestSlice = createSlice({
  name: 'dateOfInterest',
  initialState: getInitialState,
  reducers: {
    setDateOfInterest(state, action: PayloadAction<string>) {
      state.dateKey = action.payload
    }
  }
})

export const { setDateOfInterest } = dateOfInterestSlice.actions

export default dateOfInterestSlice.reducer

export const selectDateOfInterestKey = (state: RootState) => state.dateOfInterest.dateKey

export const selectDateOfInterest = createSelector([selectDateOfInterestKey], dateKey =>
  DateTime.fromISO(dateKey, { zone: ASA_GO_TIMEZONE })
)

export const resetDateOfInterestIfStale = (): AppThunk => (dispatch, getState) => {
  const todayKey = getTodayKey()
  if (!todayKey) return

  const dateOfInterestKey = selectDateOfInterestKey(getState())
  if (!dateOfInterestKey || dateOfInterestKey < todayKey) {
    dispatch(setDateOfInterest(todayKey))
  }
}
