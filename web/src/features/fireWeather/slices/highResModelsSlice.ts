import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { ModelValue, getModelsWithBiasAdj, ModelsForStation } from 'api/modelAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  allHighResModelsByStation: Record<number, ModelValue[] | undefined>
  pastHighResModelsByStation: Record<number, ModelValue[] | undefined>
  highResModelsByStation: Record<number, ModelValue[] | undefined>
}

const initialState: State = {
  loading: false,
  error: null,
  allHighResModelsByStation: {},
  pastHighResModelsByStation: {},
  highResModelsByStation: {}
}

const highResModelsSlice = createSlice({
  name: 'highResModels',
  initialState,
  reducers: {
    getHighResModelsStart(state: State) {
      state.error = null
      state.loading = true
    },
    getHighResModelsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getHighResModelsSuccess(state: State, action: PayloadAction<ModelsForStation[]>) {
      state.error = null
      action.payload.forEach(({ station, model_runs }) => {
        if (station && model_runs) {
          const code = station.code
          const pastModelValues: ModelValue[] = []
          const modelValues: ModelValue[] = []
          const allModelValues = model_runs.reduce(
            (values: ModelValue[], modelRun) => values.concat(modelRun.values),
            []
          )
          const currDate = new Date()
          allModelValues.forEach(v => {
            const isFutureModel = new Date(v.datetime) >= currDate
            if (isFutureModel) {
              modelValues.push(v)
            } else {
              pastModelValues.push(v)
            }
          })
          state.pastHighResModelsByStation[code] = pastModelValues
          state.highResModelsByStation[code] = modelValues
          state.allHighResModelsByStation[code] = allModelValues
        }
      })
      state.loading = false
    }
  }
})

export const {
  getHighResModelsStart,
  getHighResModelsFailed,
  getHighResModelsSuccess
} = highResModelsSlice.actions

export default highResModelsSlice.reducer

export const fetchHighResModels = (codes: number[]): AppThunk => async dispatch => {
  try {
    dispatch(getHighResModelsStart())
    const modelsForStations = await getModelsWithBiasAdj(codes, 'HRDPS')
    dispatch(getHighResModelsSuccess(modelsForStations))
  } catch (err) {
    dispatch(getHighResModelsFailed(err.toString()))
    logError(err)
  }
}
