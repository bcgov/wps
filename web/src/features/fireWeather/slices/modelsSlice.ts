import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { ModelValue, getModelsWithBiasAdj, ModelsForStation } from 'api/modelAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { parseModelValuesHelper } from 'features/fireWeather/slices/parseModelValuesHelper'

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
      state.allModelsByStation = {}
      state.pastModelsByStation = {}
      state.modelsByStation = {}
      state.noonModelsByStation = {}
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
          const parsedValues = parseModelValuesHelper(model_runs, true)
          state.allModelsByStation[code] = parsedValues.allValues
          state.pastModelsByStation[code] = parsedValues.pastValues
          state.modelsByStation[code] = parsedValues.modelValues
          state.noonModelsByStation[code] = parsedValues.noonValues
        }
      })
      state.loading = false
    }
  }
})

export const { getModelsStart, getModelsFailed, getModelsSuccess } = modelsSlice.actions

export default modelsSlice.reducer

export const fetchGlobalModelsWithBiasAdj = (
  codes: number[],
  timeOfInterest: string
): AppThunk => async dispatch => {
  try {
    dispatch(getModelsStart())
    const modelsForStations = await getModelsWithBiasAdj(codes, 'GDPS', timeOfInterest)
    dispatch(getModelsSuccess(modelsForStations))
  } catch (err) {
    dispatch(getModelsFailed(err.toString()))
    logError(err)
  }
}
