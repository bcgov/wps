import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { ModelType, getModelPredictions, StationPrediction } from 'api/moreCast2API'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'
import { parseModelsForStationsHelper } from 'features/moreCast2/slices/parseModelsForStationsHelper'

interface State {
  loading: boolean
  error: string | null
  stationPredictions: StationPrediction[]
  stationPredictionsAsMoreCast2ForecastRows: MoreCast2ForecastRow[]
}

const initialState: State = {
  loading: false,
  error: null,
  stationPredictions: [],
  stationPredictionsAsMoreCast2ForecastRows: []
}

// TODO - Remove raw stationPredictions from State. I think we only need the formatted data.
const modelSlice = createSlice({
  name: 'ModelSlice',
  initialState,
  reducers: {
    getModelStationPredictionsStart(state: State) {
      state.error = null
      state.stationPredictions = []
      state.stationPredictionsAsMoreCast2ForecastRows = []
      state.loading = true
    },
    getModelStationPredictionsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getModelStationPredictionsSuccess(state: State, action: PayloadAction<StationPrediction[]>) {
      state.error = null
      state.stationPredictions = action.payload
      state.stationPredictionsAsMoreCast2ForecastRows = parseModelsForStationsHelper(action.payload)
      state.loading = false
    }
  }
})

export const { getModelStationPredictionsStart, getModelStationPredictionsFailed, getModelStationPredictionsSuccess } =
  modelSlice.actions

export default modelSlice.reducer

export const getModelStationPredictions =
  (stationCodes: number[], model: ModelType, fromDate: string, toDate: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(getModelStationPredictionsStart())
      let stationPredictions: StationPrediction[] = []
      if (stationCodes.length) {
        stationPredictions = await getModelPredictions(stationCodes, model, fromDate, toDate)
      }
      dispatch(getModelStationPredictionsSuccess(stationPredictions))
    } catch (err) {
      dispatch(getModelStationPredictionsFailed((err as Error).toString()))
      logError(err)
    }
  }
