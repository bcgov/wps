import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { ModelType, getModelPredictions, StationPrediction } from 'api/moreCast2API'
import { AppThunk } from 'app/store'
import { rowIDHasher } from 'features/moreCast2/util'
import { DateTime } from 'luxon'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  stationPredictions: StationPrediction[]
}

export const initialState: State = {
  loading: false,
  error: null,
  stationPredictions: []
}

const modelSlice = createSlice({
  name: 'ModelSlice',
  initialState,
  reducers: {
    getModelStationPredictionsStart(state: State) {
      state.error = null
      state.stationPredictions = []
      state.loading = true
    },
    getModelStationPredictionsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getModelStationPredictionsSuccess(state: State, action: PayloadAction<StationPrediction[]>) {
      state.error = null
      state.stationPredictions = action.payload
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
        stationPredictions = (await getModelPredictions(stationCodes, model, fromDate, toDate)).map(pred => ({
          ...pred,
          id: rowIDHasher(pred.station.code, DateTime.fromISO(pred.datetime))
        }))
      }
      dispatch(getModelStationPredictionsSuccess(stationPredictions))
    } catch (err) {
      dispatch(getModelStationPredictionsFailed((err as Error).toString()))
      logError(err)
    }
  }
