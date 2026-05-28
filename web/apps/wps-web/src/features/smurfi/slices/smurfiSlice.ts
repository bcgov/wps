import { RootState } from '@/app/rootReducer'
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import { SpotRequestFormData } from '@wps/api/schema/spotRequestSchema'
import {
  getSpotForecasts,
  getSpotRequests,
  postSpotForecast,
  postSpotRequest,
  SpotForecastType,
  SpotForecastOutput,
  SpotRequestOutput
} from '@wps/api/SMURFIAPI'
import { AppThunk } from 'app/store'

export interface SmurfiState {
  loading: boolean
  error: string | null
  spotForecastSubmitting: boolean
  spotForecastSubmitError: string | null
  submittedSpotForecast: SpotForecastOutput | null
  spotForecastsByRequestId: Record<number, SpotForecastOutput[]>
  spotForecastsError: string | null
  spotForecastsLoading: boolean
  spotRequestSubmitting: boolean
  spotRequestSubmitError: string | null
  spotRequestsError: string | null
  spotRequestsLoading: boolean
  spotRequests: SpotRequestOutput[]
}

const initialState: SmurfiState = {
  loading: false,
  error: null,
  spotForecastSubmitting: false,
  spotForecastSubmitError: null,
  submittedSpotForecast: null,
  spotForecastsByRequestId: {},
  spotForecastsError: null,
  spotForecastsLoading: false,
  spotRequestSubmitting: false,
  spotRequestSubmitError: null,
  spotRequestsError: null,
  spotRequestsLoading: false,
  spotRequests: []
}

const smurfiSlice = createSlice({
  name: 'smurfi',
  initialState,
  reducers: {
    getSpotRequestsStart(state: SmurfiState) {
      state.spotRequestsError = null
      state.spotRequestsLoading = true
    },
    getSpotRequestsFailed(state: SmurfiState, action: PayloadAction<string>) {
      state.spotRequestsError = action.payload
      state.spotRequestsLoading = false
    },
    getSpotRequestsSuccess(state: SmurfiState, action: PayloadAction<{ spotRequests: SpotRequestOutput[] }>) {
      state.spotRequestsLoading = false
      state.spotRequestsError = null
      state.spotRequests = action.payload.spotRequests
    },
    submitSpotForecastStart(state: SmurfiState) {
      state.spotForecastSubmitError = null
      state.spotForecastSubmitting = true
    },
    submitSpotForecastFailed(state: SmurfiState, action: PayloadAction<string>) {
      state.spotForecastSubmitError = action.payload
      state.spotForecastSubmitting = false
    },
    submitSpotForecastSuccess(state: SmurfiState, action: PayloadAction<{ spotForecast: SpotForecastOutput }>) {
      state.spotForecastSubmitting = false
      state.spotForecastSubmitError = null
      state.submittedSpotForecast = action.payload.spotForecast
      state.spotForecastsByRequestId[action.payload.spotForecast.spot_request_base_id] = [
        action.payload.spotForecast,
        ...(state.spotForecastsByRequestId[action.payload.spotForecast.spot_request_base_id] ?? [])
      ]
    },
    clearSpotForecastSubmitState(state: SmurfiState) {
      state.spotForecastSubmitting = false
      state.spotForecastSubmitError = null
      state.submittedSpotForecast = null
    },
    getSpotForecastsStart(state: SmurfiState) {
      state.spotForecastsError = null
      state.spotForecastsLoading = true
    },
    getSpotForecastsFailed(state: SmurfiState, action: PayloadAction<string>) {
      state.spotForecastsError = action.payload
      state.spotForecastsLoading = false
    },
    getSpotForecastsSuccess(
      state: SmurfiState,
      action: PayloadAction<{ spotRequestId: number; spotForecasts: SpotForecastOutput[] }>
    ) {
      state.spotForecastsError = null
      state.spotForecastsLoading = false
      state.spotForecastsByRequestId[action.payload.spotRequestId] = action.payload.spotForecasts
    },
    submitSpotRequestStart(state: SmurfiState) {
      state.spotRequestSubmitError = null
      state.spotRequestSubmitting = true
    },
    submitSpotRequestFailed(state: SmurfiState, action: PayloadAction<string>) {
      state.spotRequestSubmitError = action.payload
      state.spotRequestSubmitting = false
    },
    submitSpotRequestSuccess(state: SmurfiState, action: PayloadAction<{ spotRequest: SpotRequestOutput }>) {
      state.spotRequestSubmitting = false
      state.spotRequestSubmitError = null

      // Filter out an existing spot request so it can be replaced with the updated one.
      const filteredSpotRequests = state.spotRequests.filter(sr => sr.id !== action.payload.spotRequest.id)

      state.spotRequests = [action.payload.spotRequest, ...filteredSpotRequests]
    },
    clearSpotRequestSubmitState(state: SmurfiState) {
      state.spotRequestSubmitting = false
      state.spotRequestSubmitError = null
    }
  }
})

export const {
  getSpotRequestsStart,
  getSpotRequestsFailed,
  getSpotRequestsSuccess,
  submitSpotForecastStart,
  submitSpotForecastFailed,
  submitSpotForecastSuccess,
  clearSpotForecastSubmitState,
  getSpotForecastsStart,
  getSpotForecastsFailed,
  getSpotForecastsSuccess,
  submitSpotRequestStart,
  submitSpotRequestFailed,
  submitSpotRequestSuccess,
  clearSpotRequestSubmitState
} = smurfiSlice.actions

export default smurfiSlice.reducer

export const submitSpotForecast =
  (payload: {
    formData: SpotFormData
    forecastType: SpotForecastType
    spotRequestId: number
  }): AppThunk<Promise<SpotForecastOutput | undefined>> =>
  async dispatch => {
    try {
      dispatch(submitSpotForecastStart())

      // For mini forecasts, exclude forecast summary data
      const dataToSubmit = { ...payload.formData }
      if (payload.forecastType === 'Mini') {
        delete dataToSubmit.afternoonForecast
        delete dataToSubmit.tonightForecast
        delete dataToSubmit.tomorrowForecast
      }

      const response = await postSpotForecast(dataToSubmit, payload.spotRequestId, payload.forecastType)
      dispatch(submitSpotForecastSuccess({ spotForecast: response.spot_forecast }))
      dispatch(fetchSpotRequests())
      return response.spot_forecast
    } catch (err) {
      dispatch(submitSpotForecastFailed((err as Error).toString()))
      return undefined
    }
  }

export const fetchSpotForecasts =
  (spotRequestId: number): AppThunk =>
  async dispatch => {
    try {
      dispatch(getSpotForecastsStart())
      const response = await getSpotForecasts(spotRequestId)
      dispatch(getSpotForecastsSuccess({ spotRequestId, spotForecasts: response.spot_forecasts }))
    } catch (err) {
      dispatch(getSpotForecastsFailed((err as Error).toString()))
      return []
    }
  }

export const submitSpotRequest =
  (formData: SpotRequestFormData, spotRequestId?: number): AppThunk<Promise<SpotRequestOutput | undefined>> =>
  async dispatch => {
    try {
      dispatch(submitSpotRequestStart())

      const response = await postSpotRequest(formData, spotRequestId)
      dispatch(submitSpotRequestSuccess({ spotRequest: response.spot_request }))
      return response.spot_request
    } catch (err) {
      dispatch(submitSpotRequestFailed((err as Error).toString()))
      return undefined
    }
  }

export const fetchSpotRequests = (): AppThunk => async dispatch => {
  try {
    dispatch(getSpotRequestsStart())

    const response = await getSpotRequests()
    dispatch(getSpotRequestsSuccess({ spotRequests: response.spot_requests }))
  } catch (err) {
    dispatch(getSpotRequestsFailed((err as Error).toString()))
  }
}

export const selectSmurfi = (state: RootState) => state.smurfi
