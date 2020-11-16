import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { ModelValue, getModelsWithBiasAdj, ModelsForStation } from 'api/modelAPI'
import { AppThunk } from 'app/store'
import { isNoonInPST } from 'utils/date'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  allModelsByStation: Record<number, ModelValue[] | undefined>
  pastModelsByStation: Record<number, ModelValue[] | undefined>
  modelsByStation: Record<number, ModelValue[] | undefined>
  noonModelsByStation: Record<number, ModelValue[] | undefined>
}

const initialState: State = {
  loading: false,
  error: null,
  allModelsByStation: {},
  pastModelsByStation: {},
  modelsByStation: {},
  noonModelsByStation: {}
}

const modelsSlice = createSlice({
  name: 'models',
  initialState,
  reducers: {
    getModelsStart(state: State) {
      state.error = null
      state.loading = true
    },
    getModelsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getModelsSuccess(state: State, action: PayloadAction<ModelsForStation[]>) {
      state.error = null
      action.payload.forEach(({ station, model_runs }) => {
        if (station && model_runs) {
          const code = station.code
          const pastModelValues: ModelValue[] = []
          const modelValues: ModelValue[] = []
          const noonModelValues: ModelValue[] = []
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

            if (isNoonInPST(v.datetime)) {
              noonModelValues.push(v)
            }
          })
          state.allModelsByStation[code] = allModelValues
          state.pastModelsByStation[code] = pastModelValues
          state.modelsByStation[code] = modelValues
          state.noonModelsByStation[code] = noonModelValues
        }
      })
      state.loading = false
    }
  }
})

export const { getModelsStart, getModelsFailed, getModelsSuccess } = modelsSlice.actions

export default modelsSlice.reducer

export const fetchGlobalModelsWithBiasAdj = (
  codes: number[]
): AppThunk => async dispatch => {
  try {
    dispatch(getModelsStart())
    const modelsForStations = await getModelsWithBiasAdj(codes, 'GDPS')
    dispatch(getModelsSuccess(modelsForStations))
  } catch (err) {
    dispatch(getModelsFailed(err.toString()))
    logError(err)
  }
}
