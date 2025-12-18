import { createSelector, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { groupBy, isNull, isUndefined } from 'lodash'
import { FireShapeStatusDetail, getProvincialSummary, ProvincialSummaryResponse, RunType } from 'api/fbaAPI'
import { RootState } from 'app/rootReducer'

export interface ProvincialSummaryState {
  loading: boolean
  error: string | null
  fireShapeStatusDetails: FireShapeStatusDetail[]
}

export const initialState: ProvincialSummaryState = {
  loading: false,
  error: null,
  fireShapeStatusDetails: []
}

const provincialSummarySlice = createSlice({
  name: 'provincialSummary',
  initialState,
  reducers: {
    getProvincialSummaryStart(state: ProvincialSummaryState) {
      state.error = null
      state.loading = true
      state.fireShapeStatusDetails = []
    },
    getProvincialSummaryFailed(state: ProvincialSummaryState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getProvincialSummarySuccess(state: ProvincialSummaryState, action: PayloadAction<ProvincialSummaryResponse>) {
      state.error = null
      state.fireShapeStatusDetails = action.payload.provincial_summary
      state.loading = false
    }
  }
})

export const { getProvincialSummaryStart, getProvincialSummaryFailed, getProvincialSummarySuccess } =
  provincialSummarySlice.actions

export default provincialSummarySlice.reducer

export const fetchProvincialSummary =
  (runType: RunType, run_datetime: string | null, for_date: string): AppThunk =>
  async dispatch => {
    if (!isUndefined(run_datetime) && !isNull(run_datetime)) {
      try {
        dispatch(getProvincialSummaryStart())
        const fireShapeStatuses = await getProvincialSummary(runType, run_datetime, for_date)
        dispatch(getProvincialSummarySuccess(fireShapeStatuses))
      } catch (err) {
        dispatch(getProvincialSummaryFailed((err as Error).toString()))
        logError(err)
      }
    } else {
      try {
        dispatch(getProvincialSummarySuccess({ provincial_summary: [] }))
      } catch (err) {
        dispatch(getProvincialSummaryFailed((err as Error).toString()))
        logError(err)
      }
    }
  }

const selectFireShapeStatusDetails = (state: RootState) => state.provincialSummary

export const selectProvincialSummary = createSelector([selectFireShapeStatusDetails], fireShapeStatusDetails => {
  const groupedByFireCenter = groupBy(fireShapeStatusDetails.fireShapeStatusDetails, 'fire_centre_name')
  return groupedByFireCenter
})
