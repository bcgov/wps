import { createSlice, PayloadAction } from '@reduxjs/toolkit'

export interface ReadyPlanningAreaDetails {
  id: string
  hfi_request_id: number
  planning_area_id: number
  ready: boolean
  create_timestamp: string
  create_user: string
  update_timestamp: string
  update_user: string
}

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
    // setHFIReady: (state: HFIReadyState, action: PayloadAction<FuelTypesResponse>) => {
    //   state.loading = false
    // },
    fetchHFIReadyFailed(state: HFIReadyState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    }
  }
})

export const { setHFIReadyStart, fetchHFIReadyFailed } = hfiReady.actions

export default hfiReady.reducer
