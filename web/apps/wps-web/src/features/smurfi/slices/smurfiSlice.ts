import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import { SpotRequestFormData } from '@wps/api/schema/spotRequestSchema'
import { postSpotForecast, postSpotRequest, SpotForecastOutput, SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { AppThunk } from 'app/store'

export interface SmurfiState {
  loading: boolean
  error: string | null
  spotForecastSubmitting: boolean
  spotForecastSubmitError: string | null
  submittedSpotForecast: SpotForecastOutput | null
  spotRequestSubmitting: boolean
  spotRequestSubmitError: string | null
  submittedSpotRequest: SpotRequestOutput | null
}

const initialState: SmurfiState = {
  loading: false,
  error: null,
  spotForecastSubmitting: false,
  spotForecastSubmitError: null,
  submittedSpotForecast: null,
  spotRequestSubmitting: false,
  spotRequestSubmitError: null,
  submittedSpotRequest: null
}

const smurfiSlice = createSlice({
  name: 'smurfi',
  initialState,
  reducers: {
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
    },
    clearSpotForecastSubmitState(state: SmurfiState) {
      state.spotForecastSubmitting = false
      state.spotForecastSubmitError = null
      state.submittedSpotForecast = null
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
      state.submittedSpotRequest = action.payload.spotRequest
    },
    clearSpotRequestSubmitState(state: SmurfiState) {
      state.spotRequestSubmitting = false
      state.spotRequestSubmitError = null
      state.submittedSpotRequest = null
    }
  }
})

export const {
  submitSpotForecastStart,
  submitSpotForecastFailed,
  submitSpotForecastSuccess,
  clearSpotForecastSubmitState,
  submitSpotRequestStart,
  submitSpotRequestFailed,
  submitSpotRequestSuccess,
  clearSpotRequestSubmitState
} = smurfiSlice.actions

export default smurfiSlice.reducer

export const submitSpotForecast =
  (payload: {
    formData: SpotFormData
    isMini: boolean
    spotRequestId: number
  }): AppThunk<Promise<SpotForecastOutput | undefined>> =>
  async dispatch => {
    try {
      dispatch(submitSpotForecastStart())

      // For mini forecasts, exclude forecast summary data
      const dataToSubmit = { ...payload.formData }
      if (payload.isMini) {
        delete dataToSubmit.afternoonForecast
        delete dataToSubmit.tonightForecast
        delete dataToSubmit.tomorrowForecast
      }

      const response = await postSpotForecast(dataToSubmit, payload.spotRequestId)
      dispatch(submitSpotForecastSuccess({ spotForecast: response.spot_forecast }))
      return response.spot_forecast
    } catch (err) {
      dispatch(submitSpotForecastFailed((err as Error).toString()))
      return undefined
    }
  }

export const submitSpotRequest =
  (formData: SpotRequestFormData): AppThunk<Promise<SpotRequestOutput | undefined>> =>
  async dispatch => {
    try {
      dispatch(submitSpotRequestStart())

      const response = await postSpotRequest(formData)
      dispatch(submitSpotRequestSuccess({ spotRequest: response.spot_request }))
      return response.spot_request
    } catch (err) {
      dispatch(submitSpotRequestFailed((err as Error).toString()))
      return undefined
    }
  }
