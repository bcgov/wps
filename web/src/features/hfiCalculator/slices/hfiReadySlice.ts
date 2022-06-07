import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { ReadyPlanningAreaDetails, toggleReadyState } from 'api/hfiCalculatorAPI'
import { AppThunk } from 'app/store'
import { AxiosError } from 'axios'
import { logError } from 'utils/error'

export interface HFIReadyState {
  loading: boolean
  error: string | null
  planningAreaReadyDetails: { [key: string]: ReadyPlanningAreaDetails }
}

export const initialState: HFIReadyState = {
  loading: false,
  error: null,
  planningAreaReadyDetails: {}
}

const hfiReady = createSlice({
  name: 'hfiReady',
  initialState,
  reducers: {
    setHFIReadyStart(state: HFIReadyState) {
      state.loading = true
    },
    setHFIToggleReadyState(state: HFIReadyState, action: PayloadAction<ReadyPlanningAreaDetails>) {
      state.loading
      state.planningAreaReadyDetails[action.payload.planning_area_id] = action.payload
    },
    setHFIReadyFailed(state: HFIReadyState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    }
  }
})

export const { setHFIReadyStart, setHFIToggleReadyState, setHFIReadyFailed } = hfiReady.actions

export default hfiReady.reducer

export const fetchToggleReadyState =
  (planning_area_id: number, hfi_request_id: number): AppThunk =>
  async dispatch => {
    try {
      dispatch(setHFIReadyStart())
      const readyState = await toggleReadyState(planning_area_id, hfi_request_id)
      dispatch(setHFIToggleReadyState(readyState))
    } catch (err) {
      const { response } = err as AxiosError
      dispatch(setHFIReadyFailed(response?.data.detail))
      logError(err)
    }
  }
