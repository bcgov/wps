import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { ModelRun, ModelRuns, getModelRuns, getCHainesGeoJSON } from 'api/cHainesAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FeatureCollection } from 'geojson'

interface State {
  loading: boolean
  error: string | null
  model_runs: ModelRun[]
  model_run_predictions: Record<string, Record<string, Record<string, FeatureCollection>>>
  model_run_predictions_status: Record<string, Record<string, Record<string, string>>>
  selected_model_abbreviation: string
  // TODO: rename selected_model_timestamp to selected_model_run_timestamp
  selected_model_timestamp: string
  selected_prediction_timestamp: string
}

interface GeoJSONContext {
  model: string
  model_run_timestamp: string
  prediction_timestamp: string
  result: FeatureCollection
}

const initialState: State = {
  loading: false,
  error: null,
  model_runs: [],
  selected_model_abbreviation: 'GDPS',
  selected_model_timestamp: '',
  selected_prediction_timestamp: '',
  model_run_predictions: {},
  model_run_predictions_status: {}
}

const cHainesModelRunsSlice = createSlice({
  name: 'c-haines-model-runs',
  initialState: initialState,
  reducers: {
    getModelRunsStart(state: State) {
      state.loading = true
      state.selected_prediction_timestamp = ''
    },
    getModelRunsSuccess(state: State, action: PayloadAction<ModelRuns>) {
      state.model_runs = action.payload.model_runs
      if (state.model_runs.length > 0) {
        state.selected_model_abbreviation = state.model_runs[0].model.abbrev
        state.selected_model_timestamp = state.model_runs[0].model_run_timestamp
        if (state.model_runs[0].prediction_timestamps.length > 0) {
          state.selected_prediction_timestamp =
            state.model_runs[0].prediction_timestamps[0]
        }
      }
      state.model_runs.forEach(e => {
        state.model_run_predictions[e.model_run_timestamp] = {}
      })
      state.loading = false
      state.error = null
    },
    getModelRunsFailed(state: State, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    setSelectedModel(state: State, action: PayloadAction<string>) {
      state.selected_model_abbreviation = action.payload
      const model_run = state.model_runs.find(
        model_run => model_run.model.abbrev === action.payload
      )
      if (model_run) {
        state.selected_model_timestamp = model_run.model_run_timestamp
        if (model_run.prediction_timestamps.length > 0) {
          state.selected_prediction_timestamp = model_run.prediction_timestamps[0]
        }
      } else {
        state.selected_model_timestamp = ''
      }
    },
    setSelectedModelRun(state: State, action: PayloadAction<string>) {
      state.selected_model_timestamp = action.payload
      const model_run = state.model_runs.find(
        model_run =>
          model_run.model_run_timestamp === action.payload &&
          model_run.model.abbrev === state.selected_model_abbreviation
      )
      if (model_run) {
        state.selected_prediction_timestamp = model_run.prediction_timestamps[0]
      } else {
        state.selected_prediction_timestamp = ''
      }
    },
    setSelectedPrediction(state: State, action: PayloadAction<string>) {
      console.log('setSelectedPrediction', action.payload)
      state.selected_prediction_timestamp = action.payload
    },
    getPredictionStart(state: State) {
      state.loading = true
    },
    getPredictionSuccess(state: State, action: PayloadAction<GeoJSONContext>) {
      console.log('getPredictionSuccess', action.payload.model, action.payload.result)
      if (!(action.payload.model in state.model_run_predictions)) {
        state.model_run_predictions[action.payload.model] = {}
      }
      if (
        !(
          action.payload.model_run_timestamp in
          state.model_run_predictions[action.payload.model]
        )
      ) {
        state.model_run_predictions[action.payload.model][
          action.payload.model_run_timestamp
        ] = {}
      }
      state.model_run_predictions[action.payload.model][
        action.payload.model_run_timestamp
      ][action.payload.prediction_timestamp] = action.payload.result
    },
    getPredictionFailed(state: State, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    }
  }
})

const {
  getModelRunsStart,
  getModelRunsSuccess,
  getModelRunsFailed,
  setSelectedModel,
  setSelectedModelRun,
  setSelectedPrediction,
  getPredictionStart,
  getPredictionSuccess,
  getPredictionFailed
} = cHainesModelRunsSlice.actions

export default cHainesModelRunsSlice.reducer

export const fetchModelRuns = (): AppThunk => async dispatch => {
  try {
    dispatch(getModelRunsStart())
    const modelsRuns = await getModelRuns()
    dispatch(getModelRunsSuccess(modelsRuns))
    // if (modelsRuns.model_runs.length > 0) {
    //   if (modelsRuns.model_runs[0].prediction_timestamps[0])
    //   dispatch(
    //     fetchCHainesGeoJSON(
    //       modelsRuns.model_runs[0].model_run_timestamp,
    //       modelsRuns.model_runs[0].prediction_timestamps[0]
    //     )
    //   )
    // }
  } catch (err) {
    dispatch(getModelRunsFailed(err.toString()))
    logError(err)
  }
}

export const updateSelectedModel = (
  selected_model: string
): AppThunk => async dispatch => {
  dispatch(setSelectedModel(selected_model))
}
export const updateSelectedModelRun = (
  selected_model_run_timestamp: string
): AppThunk => async dispatch => {
  dispatch(setSelectedModelRun(selected_model_run_timestamp))
}

export const updateSelectedPrediction = (
  selected_prediction_timestamp: string
): AppThunk => async dispatch => {
  dispatch(setSelectedPrediction(selected_prediction_timestamp))
}

export const fetchCHainesGeoJSON = (
  model_abbreviation: string,
  model_run_timestamp: string,
  prediction_timestamp: string
): AppThunk => async dispatch => {
  try {
    dispatch(getPredictionStart())
    const geoJSON = await getCHainesGeoJSON(
      model_abbreviation,
      model_run_timestamp,
      prediction_timestamp
    )
    const result = {
      model: model_abbreviation,
      model_run_timestamp: model_run_timestamp,
      prediction_timestamp: prediction_timestamp,
      result: geoJSON
    }
    dispatch(getPredictionSuccess(result))
  } catch (err) {
    dispatch(getPredictionFailed(err.toString()))
    logError(err)
  }
}
