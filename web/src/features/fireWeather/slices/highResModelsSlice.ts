import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { ModelValue, getModelsWithBiasAdj, ModelsForStation } from 'api/modelAPI'
import { parseModelValuesHelper } from 'features/fireWeather/slices/parseModelValuesHelper'
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
      state.allHighResModelsByStation = {}
      state.pastHighResModelsByStation = {}
      state.highResModelsByStation = {}
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
          const parsedValues = parseModelValuesHelper(model_runs, false)
          state.pastHighResModelsByStation[code] = parsedValues.pastValues
          state.highResModelsByStation[code] = parsedValues.modelValues
          state.allHighResModelsByStation[code] = parsedValues.allValues
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

export const fetchHighResModels = (
  codes: number[],
  timeOfInterest: string
): AppThunk => async dispatch => {
  try {
    dispatch(getHighResModelsStart())
    const modelsForStations = await getModelsWithBiasAdj(codes, 'HRDPS', timeOfInterest)
    dispatch(getHighResModelsSuccess(modelsForStations))
  } catch (err) {
    dispatch(getHighResModelsFailed(err.toString()))
    logError(err)
  }
}
