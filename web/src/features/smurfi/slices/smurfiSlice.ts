import { postSpotForecast, SpotForecastOutput } from '@/api/SMURFIAPI'
import { FormData } from '@/features/smurfi/schemas/spotForecastSchema'
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'

export interface SmurfiState {
  loading: boolean
  error: string | null
  spotForecastSubmitting: boolean
  spotForecastSubmitError: string | null
  submittedSpotForecast: SpotForecastOutput | null
}

const initialState: SmurfiState = {
  loading: false,
  error: null,
  spotForecastSubmitting: false,
  spotForecastSubmitError: null,
  submittedSpotForecast: null
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
    }
  }
})

export const {
  submitSpotForecastStart,
  submitSpotForecastFailed,
  submitSpotForecastSuccess,
  clearSpotForecastSubmitState
} = smurfiSlice.actions

export default smurfiSlice.reducer

export const submitSpotForecast =
  (payload: { formData: FormData; isMini: boolean }): AppThunk =>
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

      const response = await postSpotForecast(dataToSubmit)
      dispatch(submitSpotForecastSuccess({ spotForecast: response.spot_forecast }))
    } catch (err) {
      dispatch(submitSpotForecastFailed((err as Error).toString()))
    }
  }
