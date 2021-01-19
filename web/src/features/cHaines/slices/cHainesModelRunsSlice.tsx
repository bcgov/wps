import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { ModelRun, ModelRuns, getModelRuns, getCHainesGeoJSON } from 'api/cHainesAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FeatureCollection } from 'geojson'

interface State {
  loading: boolean
  error: string | null
  model_runs: ModelRun[]
  model_run_predictions: Record<string, Record<string, FeatureCollection>>
  selected_model: string
}

interface GeoJSONContext {
  model_run_timestamp: string
  prediction_timestamp: string
  result: FeatureCollection
}

const initialState: State = {
  loading: false,
  error: null,
  model_runs: [],
  selected_model: '',
  model_run_predictions: {}
}

const cHainesModelRunsSlice = createSlice({
  name: 'c-haines-model-runs',
  initialState: initialState,
  reducers: {
    getModelRunsStart(state: State) {
      state.loading = true
    },
    getModelRunsSuccess(state: State, action: PayloadAction<ModelRuns>) {
      state.model_runs = action.payload.model_runs
      state.selected_model =
        state.model_runs.length > 0 ? state.model_runs[0].model_run_timestamp : ''
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
      state.selected_model = action.payload
    },
    getPredictionStart(state: State) {
      state.loading = true
    },
    getPredictionSuccess(state: State, action: PayloadAction<GeoJSONContext>) {
      state.model_run_predictions[action.payload.model_run_timestamp][
        action.payload.prediction_timestamp
      ] = action.payload.result
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

export const fetchCHainesGeoJSON = (
  model_run_timestamp: string,
  prediction_timestamp: string
): AppThunk => async dispatch => {
  try {
    dispatch(getPredictionStart())
    const geoJSON = await getCHainesGeoJSON(model_run_timestamp, prediction_timestamp)
    const result = {
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
