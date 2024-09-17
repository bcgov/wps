import { createSelector, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { groupBy, isNull, isUndefined } from 'lodash'
import { FireShapeAreaDetail, getProvincialSummary, ProvincialSummaryResponse, RunType } from 'api/fbaAPI'
import { RootState } from 'app/rootReducer'

export interface ProvincialSummaryState {
  loading: boolean
  error: string | null
  fireShapeAreaDetails: FireShapeAreaDetail[]
}

export const initialState: ProvincialSummaryState = {
  loading: false,
  error: null,
  fireShapeAreaDetails: []
}

const provincialSummarySlice = createSlice({
  name: 'provincialSummary',
  initialState,
  reducers: {
    getProvincialSummaryStart(state: ProvincialSummaryState) {
      state.error = null
      state.loading = true
      state.fireShapeAreaDetails = []
    },
    getProvincialSummaryFailed(state: ProvincialSummaryState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getProvincialSummarySuccess(state: ProvincialSummaryState, action: PayloadAction<ProvincialSummaryResponse>) {
      state.error = null
      state.fireShapeAreaDetails = action.payload.provincial_summary
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
        const fireShapeAreas = await getProvincialSummary(runType, run_datetime, for_date)
        dispatch(getProvincialSummarySuccess(fireShapeAreas))
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

const selectFireShapeAreaDetails = (state: RootState) => state.provincialSummary

export const selectProvincialSummary = createSelector([selectFireShapeAreaDetails], fireShapeAreaDetails => {
  const groupedByFireCenter = groupBy(fireShapeAreaDetails.fireShapeAreaDetails, 'fire_centre_name')
  return groupedByFireCenter
})
