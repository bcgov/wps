import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { parseModelValuesSlice } from 'features/fireWeather/slices/parseModelValuesSlice'
import { ModelValue, getModelsWithBiasAdj, ModelsForStation } from 'api/modelAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  allRegionalModelsByStation: Record<number, ModelValue[] | undefined>
  pastRegionalModelsByStation: Record<number, ModelValue[] | undefined>
  regionalModelsByStation: Record<number, ModelValue[] | undefined>
}

const initialState: State = {
  loading: false,
  error: null,
  allRegionalModelsByStation: {},
  pastRegionalModelsByStation: {},
  regionalModelsByStation: {}
}

const regionalModelsSlice = createSlice({
  name: 'regionalModels',
  initialState,
  reducers: {
    getRegionalModelsStart(state: State) {
      state.error = null
      state.loading = true
    },
    getRegionalModelsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getRegionalModelsSuccess(state: State, action: PayloadAction<ModelsForStation[]>) {
      state.error = null
      action.payload.forEach(({ station, model_runs }) => {
        if (station && model_runs) {
          const code = station.code
          const parsedValues = parseModelValuesSlice(model_runs, false)
          state.pastRegionalModelsByStation[code] = parsedValues.pastValues
          state.regionalModelsByStation[code] = parsedValues.modelValues
          state.allRegionalModelsByStation[code] = parsedValues.allValues
        }
      })
      state.loading = false
    }
  }
})

export const {
  getRegionalModelsStart: getRegionalModelsStart,
  getRegionalModelsFailed: getRegionalModelsFailed,
  getRegionalModelsSuccess: getRegionalModelsSuccess
} = regionalModelsSlice.actions

export default regionalModelsSlice.reducer

export const fetchRegionalModels = (codes: number[]): AppThunk => async dispatch => {
  try {
    dispatch(getRegionalModelsStart())
    const modelsForStations = await getModelsWithBiasAdj(codes, 'RDPS')
    dispatch(getRegionalModelsSuccess(modelsForStations))
  } catch (err) {
    dispatch(getRegionalModelsFailed(err.toString()))
    logError(err)
  }
}
