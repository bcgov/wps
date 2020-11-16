import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { ModelSummary, getModelSummaries, ModelSummariesForStation } from 'api/modelAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  modelSummariesByStation: Record<number, ModelSummary[] | undefined>
}

const initialState: State = {
  loading: false,
  error: null,
  modelSummariesByStation: {}
}

const modelSummariesSlice = createSlice({
  name: 'modelSummaries',
  initialState,
  reducers: {
    getModelSummariesStart(state: State) {
      state.error = null
      state.loading = true
    },
    getModelSummariesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getModelSummariesSuccess(
      state: State,
      action: PayloadAction<ModelSummariesForStation[]>
    ) {
      state.error = null
      action.payload.forEach(summary => {
        if (summary.station) {
          const code = summary.station.code
          state.modelSummariesByStation[code] = summary.values
        }
      })
      state.loading = false
    }
  }
})

export const {
  getModelSummariesStart,
  getModelSummariesFailed,
  getModelSummariesSuccess
} = modelSummariesSlice.actions

export default modelSummariesSlice.reducer

export const fetchGlobalModelSummaries = (
  stationCodes: number[]
): AppThunk => async dispatch => {
  try {
    dispatch(getModelSummariesStart())
    const modelSummaries = await getModelSummaries(stationCodes, 'GDPS')
    dispatch(getModelSummariesSuccess(modelSummaries))
  } catch (err) {
    dispatch(getModelSummariesFailed(err.toString()))
    logError(err)
  }
}
