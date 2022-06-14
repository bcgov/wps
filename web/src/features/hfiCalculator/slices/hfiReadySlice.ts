import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { getAllReadyStates, ReadyPlanningAreaDetails, toggleReadyState } from 'api/hfiCalculatorAPI'
import { AppThunk } from 'app/store'
import { AxiosError } from 'axios'
import { PrepDateRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { logError } from 'utils/error'

export interface HFIReadyState {
  loading: boolean
  error: string | null
  readyToggleSuccess: boolean
  planningAreaReadyDetails: { [key: string]: ReadyPlanningAreaDetails }
}

export const initialState: HFIReadyState = {
  loading: false,
  error: null,
  readyToggleSuccess: false,
  planningAreaReadyDetails: {}
}

const buildPlanningAreaDetails = (details: ReadyPlanningAreaDetails[]): { [key: string]: ReadyPlanningAreaDetails } => {
  return Object.assign({}, ...details.map(detail => ({ [detail.planning_area_id]: detail })))
}

const hfiReady = createSlice({
  name: 'hfiReady',
  initialState,
  reducers: {
    setHFIReadyStart(state: HFIReadyState) {
      state.loading = true
      state.readyToggleSuccess = false
    },
    setHFIToggleReadyState(state: HFIReadyState, action: PayloadAction<ReadyPlanningAreaDetails>) {
      state.loading = false
      state.readyToggleSuccess = true
      state.planningAreaReadyDetails[action.payload.planning_area_id] = { ...action.payload }
    },
    setAllReadyStates(state: HFIReadyState, action: PayloadAction<ReadyPlanningAreaDetails[]>) {
      state.loading = false
      state.planningAreaReadyDetails = buildPlanningAreaDetails(action.payload)
    },
    setHFIReadyFailed(state: HFIReadyState, action: PayloadAction<string>) {
      state.loading = false
      state.readyToggleSuccess = false
      state.error = action.payload
    },
    setToggleSuccess(state: HFIReadyState, action: PayloadAction<boolean>) {
      state.readyToggleSuccess = action.payload
    }
  }
})

export const { setHFIReadyStart, setHFIToggleReadyState, setAllReadyStates, setToggleSuccess, setHFIReadyFailed } =
  hfiReady.actions

export default hfiReady.reducer

export const fetchToggleReadyState =
  (fire_centre_id: number, planning_area_id: number, date_range: PrepDateRange): AppThunk =>
  async dispatch => {
    try {
      dispatch(setHFIReadyStart())
      const readyState = await toggleReadyState(
        fire_centre_id,
        planning_area_id,
        date_range.start_date,
        date_range.end_date
      )
      dispatch(setHFIToggleReadyState(readyState))
    } catch (err) {
      const { response } = err as AxiosError
      dispatch(setHFIReadyFailed(response?.data.detail))
      logError(err)
    }
  }

export const fetchAllReadyStates =
  (fire_centre_id: number, date_range: PrepDateRange): AppThunk =>
  async dispatch => {
    try {
      dispatch(setHFIReadyStart())
      const readyStates = await getAllReadyStates(fire_centre_id, date_range.start_date, date_range.end_date)
      dispatch(setAllReadyStates(readyStates))
    } catch (err) {
      const { response } = err as AxiosError
      dispatch(setHFIReadyFailed(response?.data.detail))
      logError(err)
    }
  }
