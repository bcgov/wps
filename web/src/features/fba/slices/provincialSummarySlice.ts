import { createSelector, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { groupBy } from 'lodash'
import { FireShapeAreaDetail, getProvincialSummary, ProvincialSummaryResponse } from 'api/fbaAPI'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'
import { RootState } from 'app/rootReducer'

interface State {
  loading: boolean
  error: string | null
  fireShapeAreaDetails: FireShapeAreaDetail[]
}

const initialState: State = {
  loading: false,
  error: null,
  fireShapeAreaDetails: []
}

const provincialSummarySlice = createSlice({
  name: 'provincialSummary',
  initialState,
  reducers: {
    getProvincialSummaryStart(state: State) {
      state.error = null
      state.loading = true
      state.fireShapeAreaDetails = []
    },
    getProvincialSummaryFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getProvincialSummarySuccess(state: State, action: PayloadAction<ProvincialSummaryResponse>) {
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
  (runType: RunType, run_datetime: string, for_date: string): AppThunk =>
    async dispatch => {
      if (run_datetime != undefined && run_datetime !== ``) {
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
          dispatch(getProvincialSummaryFailed('run_datetime cannot be undefined!'))
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
