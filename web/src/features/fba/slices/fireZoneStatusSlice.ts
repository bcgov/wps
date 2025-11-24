import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FireZoneStatus, FireZoneStatusListResponse, getZoneAdvisoryStatus, RunType } from 'api/fbaAPI'
import { isNull, isUndefined } from 'lodash'

export interface FireZoneStatusState {
  loading: boolean
  error: string | null
  fireZoneStatuses: FireZoneStatus[]
}

export const initialState: FireZoneStatusState = {
  loading: false,
  error: null,
  fireZoneStatuses: []
}

const fireZoneStatusSlice = createSlice({
  name: 'fireZoneStatuses',
  initialState,
  reducers: {
    getFireZoneStatusesStart(state: FireZoneStatusState) {
      state.error = null
      state.loading = true
      state.fireZoneStatuses = []
    },
    getFireZoneStatusesFailed(state: FireZoneStatusState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireZoneStatusesSuccess(state: FireZoneStatusState, action: PayloadAction<FireZoneStatusListResponse>) {
      state.error = null
      state.fireZoneStatuses = action.payload.zones
      state.loading = false
    }
  }
})

export const { getFireZoneStatusesStart, getFireZoneStatusesFailed, getFireZoneStatusesSuccess } =
  fireZoneStatusSlice.actions

export default fireZoneStatusSlice.reducer

export const fetchFireZoneStatuses =
  (runType: RunType, run_datetime: string | null, for_date: string): AppThunk =>
  async dispatch => {
    if (!isUndefined(run_datetime) && !isNull(run_datetime)) {
      try {
        dispatch(getFireZoneStatusesStart())
        const fireZoneStatuses = await getZoneAdvisoryStatus(runType, run_datetime, for_date)
        dispatch(getFireZoneStatusesSuccess(fireZoneStatuses))
      } catch (err) {
        dispatch(getFireZoneStatusesFailed((err as Error).toString()))
        logError(err)
      }
    } else {
      try {
        dispatch(getFireZoneStatusesSuccess({ zones: [] }))
      } catch (err) {
        dispatch(getFireZoneStatusesFailed((err as Error).toString()))
        logError(err)
      }
    }
  }
