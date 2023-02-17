import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { ModelType, getModelPredictions } from 'api/nextCastAPI'
import { ModelsForStation } from 'api/modelAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { NextCastForecastRow } from 'features/moreCast2/interfaces'
import { parseModelsForStationsHelper } from 'features/moreCast2/slices/parseModelsForStationsHelper'

interface State {
  loading: boolean
  error: string | null
  stationPredictions: ModelsForStation[]
  stationPredictionsAsNextCastForecastRows: NextCastForecastRow[]
}

const initialState: State = {
  loading: false,
  error: null,
  stationPredictions: [],
  stationPredictionsAsNextCastForecastRows: []
}

const modelSlice = createSlice({
  name: 'ModelSlice',
  initialState,
  reducers: {
    getModelStationPredictionsStart(state: State) {
      state.error = null
      state.stationPredictions = []
      state.stationPredictionsAsNextCastForecastRows = []
      state.loading = true
    },
    getModelStationPredictionsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getModelStationPredictionsSuccess(state: State, action: PayloadAction<ModelsForStation[]>) {
      state.error = null
      state.stationPredictions = action.payload
      state.stationPredictionsAsNextCastForecastRows = parseModelsForStationsHelper(action.payload)
      state.loading = false
    }
  }
})

export const { getModelStationPredictionsStart, getModelStationPredictionsFailed, getModelStationPredictionsSuccess } =
  modelSlice.actions

export default modelSlice.reducer

export const getModelStationPredictions =
  (stationCodes: number[], model: ModelType, fromDate: number, toDate: number): AppThunk =>
  async dispatch => {
    try {
      dispatch(getModelStationPredictionsStart())
      let stationPredictions: ModelsForStation[] = []
      if (stationCodes.length) {
        stationPredictions = await getModelPredictions(stationCodes, model, fromDate, toDate)
      }
      dispatch(getModelStationPredictionsSuccess(stationPredictions))
    } catch (err) {
      dispatch(getModelStationPredictionsFailed((err as Error).toString()))
      logError(err)
    }
  }
