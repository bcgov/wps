import { GridColDef } from '@mui/x-data-grid'
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { ModelType, getModelPredictions, StationPrediction, ModelChoice } from 'api/moreCast2API'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  colField: string | null
  modelChoice: ModelChoice | null
  stationPredictions: StationPrediction[]
}

const initialState: State = {
  loading: false,
  error: null,
  colField: null,
  modelChoice: null,
  stationPredictions: []
}

const columnModelSlice = createSlice({
  name: 'ColumnModelSlice',
  initialState,
  reducers: {
    getColumnModelStationPredictionsStart(state: State) {
      state.error = null
      state.stationPredictions = []
      state.loading = true
    },
    getColumnModelStationPredictionsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getColumnModelStationPredictionsSuccess(
      state: State,
      action: PayloadAction<{ colField: string; predictions: StationPrediction[] }>
    ) {
      state.error = null
      state.stationPredictions = action.payload.predictions
      state.colField = action.payload.colField
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
  (stationCodes: number[], model: ModelType, colDef: GridColDef, fromDate: string, toDate: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(getColumnModelStationPredictionsStart())
      let stationPredictions: StationPrediction[] = []
      if (stationCodes.length) {
        stationPredictions = await getModelPredictions(stationCodes, model, fromDate, toDate)
      }
      dispatch(getColumnModelStationPredictionsSuccess({ colField: colDef.field, predictions: stationPredictions }))
    } catch (err) {
      dispatch(getColumnModelStationPredictionsFailed((err as Error).toString()))
      logError(err)
    }
  }
