import { RootState } from '@/app/rootReducer'
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
  spotRequests: SpotRequestOutput[]
}

const initialState: SmurfiState = {
  loading: false,
  error: null,
  spotForecastSubmitting: false,
  spotForecastSubmitError: null,
  submittedSpotForecast: null,
  spotRequestSubmitting: false,
  spotRequestSubmitError: null,
  spotRequests: []
  // spotRequests: [
  //   {
  //     id: 1,
  //     requestReference: 'foo',
  //     fireNumber: 'V001234567',
  //     fireCentre: 'Coastal',
  //     status: SpotRequestStatus.NEW,
  //     requestorName: 'Darren',
  //     requestorIDIR: 'IDIR/DRN',
  //     requestorEmail: 'drn.bos@gov.bc.ca',
  //     requestFrequency: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
  //     requestType: SpotRequestType.MINI_SPOT,
  //     slopeAspect: 'Northwest',
  //     elevation: 1101,
  //     geographicDescription: 'Strathcona',
  //     latitude: 49,
  //     longitude: -121,
  //     requestedAt: '2026-05-19T00:00-07:00',
  //     forecastStartDate: '2026-05-20T00:00-07:00',
  //     forecastEndDate: '2026-05-27T00:00-07:00',
  //     emailDistributionList: ['drn.bos@gov.bc.ca']
  //   },
  //   {
  //     id: 2,
  //     requestReference: 'bar',
  //     fireNumber: 'K001234567',
  //     fireCentre: 'Kamloops',
  //     status: SpotRequestStatus.ACTIVE,
  //     requestorName: 'Aaron',
  //     requestorIDIR: 'IDIR/ARN',
  //     requestorEmail: 'arn@gov.bc.ca',
  //     requestFrequency: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
  //     requestType: SpotRequestType.FULL_SPOT,
  //     slopeAspect: 'West',
  //     elevation: 507,
  //     geographicDescription: 'Grasslands',
  //     latitude: 49.5,
  //     longitude: -120,
  //     requestedAt: '2026-05-19T00:00-07:00',
  //     forecastStartDate: '2026-05-20T00:00-07:00',
  //     forecastEndDate: '2026-05-30T00:00-07:00',
  //     emailDistributionList: ['arn@gov.bc.ca']
  //   },
  //   {
  //     id: 3,
  //     requestReference: 'dog',
  //     fireNumber: 'G001234567',
  //     fireCentre: 'Prince George',
  //     status: SpotRequestStatus.PAUSED,
  //     requestorName: 'Jon',
  //     requestorIDIR: 'IDIR/DRN',
  //     requestorEmail: 'jon@gov.bc.ca',
  //     requestFrequency: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
  //     requestType: SpotRequestType.FULL_SPOT,
  //     slopeAspect: 'East',
  //     elevation: 603,
  //     geographicDescription: 'Snow',
  //     latitude: 50,
  //     longitude: -123.5,
  //     requestedAt: '2026-05-19T00:00-07:00',
  //     forecastStartDate: '2026-05-20T00:00-07:00',
  //     forecastEndDate: '2026-05-27T00:00-07:00',
  //     emailDistributionList: ['jon@gov.bc.ca']
  //   }
  // ]
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
  (payload: { formData: SpotFormData; isMini: boolean }): AppThunk =>
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

export const selectSpotForecasts = (state: RootState) => state.smurfi.spotRequests
