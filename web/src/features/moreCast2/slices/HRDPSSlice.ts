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
  stationPredictionsHRDPS: ModelsForStation[]
  stationPredictionsAsNextCastForecastRows: NextCastForecastRow[]
}

const initialState: State = {
  loading: false,
  error: null,
  stationPredictionsHRDPS: [],
  stationPredictionsAsNextCastForecastRows: []
}

const HRDPSSlice = createSlice({
  name: 'HRDPSStationPredictions',
  initialState,
  reducers: {
    getHRDPSStationPredictionsStart(state: State) {
      state.error = null
      state.stationPredictionsHRDPS = []
      state.stationPredictionsAsNextCastForecastRows = []
      state.loading = true
    },
    getHRDPSStationPredictionsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getHRDPSStationPredictionsSuccess(state: State, action: PayloadAction<ModelsForStation[]>) {
      state.error = null
      state.stationPredictionsHRDPS = action.payload
      state.stationPredictionsAsNextCastForecastRows = parseModelsForStationsHelper(action.payload)
      state.loading = false
    }
  }
})

export const { getHRDPSStationPredictionsStart, getHRDPSStationPredictionsFailed, getHRDPSStationPredictionsSuccess } =
  HRDPSSlice.actions

export default HRDPSSlice.reducer

export const getHRDPSStationPredictions =
  (stationCodes: number[], model: ModelType, fromDate: number, toDate: number): AppThunk =>
  async dispatch => {
    try {
      dispatch(getHRDPSStationPredictionsStart())
      let stationPredictions: ModelsForStation[] = []
      if (stationCodes.length) {
        stationPredictions = await getModelPredictions(stationCodes, model, fromDate, toDate)
      }
      dispatch(getHRDPSStationPredictionsSuccess(stationPredictions))
    } catch (err) {
      dispatch(getHRDPSStationPredictionsFailed((err as Error).toString()))
      logError(err)
    }
  }
