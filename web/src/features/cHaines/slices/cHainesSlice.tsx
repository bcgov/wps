import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { ModelRun, ModelRuns, getModelRuns } from 'api/cHainesAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface CHainesState {
  loading: boolean
  error: string | null
  model_runs: ModelRun[]
}

const initialState: CHainesState = {
  loading: false,
  error: null,
  model_runs: []
}

const cHainesModelRunsSlice = createSlice({
  name: 'c-haines',
  initialState: initialState,
  reducers: {
    getModelRunsStart(state: CHainesState) {
      state.loading = true
    },
    getModelRunsSuccess(state: CHainesState, action: PayloadAction<ModelRuns>) {
      state.model_runs = action.payload.model_runs
      state.loading = false
      state.error = null
    },
    getModelRunsFailed(state: CHainesState, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    }
  }
})

const {
  getModelRunsStart,
  getModelRunsSuccess,
  getModelRunsFailed
} = cHainesModelRunsSlice.actions

export default cHainesModelRunsSlice.reducer

export const fetchModelRuns = (): AppThunk => async dispatch => {
  try {
    dispatch(getModelRunsStart())
    const modelsRuns = await getModelRuns()
    dispatch(getModelRunsSuccess(modelsRuns))
  } catch (err) {
    dispatch(getModelRunsFailed(err.toString()))
    logError(err)
  }
}
