import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { ModelType, getModelPredictions, StationPrediction } from 'api/moreCast2API'
import { AppThunk } from 'app/store'
import { ColField, MoreCast2ForecastRow } from 'features/moreCast2/interfaces'
import { rowIDHasher } from 'features/moreCast2/util'
import { DateTime } from 'luxon'
import { logError } from 'utils/error'

export interface ColPrediction {
  colField: ColField
  modelType: ModelType
  stationPredictions: StationPrediction[]
}

interface State {
  loading: boolean
  error: string | null
  colPrediction: ColPrediction | null
}

const initialState: State = {
  loading: false,
  error: null,
  colPrediction: null
}

const columnModelSlice = createSlice({
  name: 'ColumnModelSlice',
  initialState,
  reducers: {
    getColumnModelStationPredictionsStart(state: State) {
      state.error = null
      state.loading = true
    },
    getColumnModelStationPredictionsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getColumnModelStationPredictionsSuccess(state: State, action: PayloadAction<ColPrediction>) {
      state.error = null
      state.colPrediction = action.payload
      state.loading = false
    }
  }
})

export const {
  getColumnModelStationPredictionsStart,
  getColumnModelStationPredictionsFailed,
  getColumnModelStationPredictionsSuccess
} = columnModelSlice.actions

export default columnModelSlice.reducer

export const getColumnModelStationPredictions =
  (
    stationCodes: number[],
    model: ModelType,
    colField: keyof MoreCast2ForecastRow,
    fromDate: string,
    toDate: string
  ): AppThunk =>
  async dispatch => {
    try {
      dispatch(getColumnModelStationPredictionsStart())
      let stationPredictions: StationPrediction[] = []
      if (stationCodes.length) {
        stationPredictions = (await getModelPredictions(stationCodes, model, fromDate, toDate)).map(pred => ({
          ...pred,
          id: rowIDHasher(pred.station.code, DateTime.fromISO(pred.datetime))
        }))
      }
      dispatch(
        getColumnModelStationPredictionsSuccess({
          colField: colField,
          modelType: model,
          stationPredictions
        })
      )
    } catch (err) {
      dispatch(getColumnModelStationPredictionsFailed((err as Error).toString()))
      logError(err)
    }
  }
