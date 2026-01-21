import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { getClimatology } from 'api/climatologyAPI'
import { AppThunk } from 'app/store'
import { AggregationPeriod, ClimatologyResponse, ReferencePeriod, WeatherVariable } from '../interfaces'
import { logError } from 'utils/error'

export interface ClimatologyState {
  loading: boolean
  error: string | null
  result: ClimatologyResponse | null
}

export const climatologyInitialState: ClimatologyState = {
  loading: false,
  error: null,
  result: null
}

const climatologySlice = createSlice({
  name: 'climatology',
  initialState: climatologyInitialState,
  reducers: {
    getClimatologyStart(state: ClimatologyState) {
      state.loading = true
      state.error = null
    },
    getClimatologySuccess(state: ClimatologyState, action: PayloadAction<ClimatologyResponse>) {
      state.result = action.payload
      state.loading = false
      state.error = null
    },
    getClimatologyFailed(state: ClimatologyState, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    resetClimatologyResult(state: ClimatologyState) {
      state.result = null
      state.error = null
    }
  }
})

export const { getClimatologyStart, getClimatologyFailed, getClimatologySuccess, resetClimatologyResult } =
  climatologySlice.actions

export default climatologySlice.reducer

export const fetchClimatology =
  (
    stationCode: number,
    variable: WeatherVariable,
    aggregation: AggregationPeriod,
    referencePeriod: ReferencePeriod,
    comparisonYear?: number
  ): AppThunk =>
  async dispatch => {
    try {
      dispatch(getClimatologyStart())
      const result = await getClimatology(stationCode, variable, aggregation, referencePeriod, comparisonYear)
      dispatch(getClimatologySuccess(result))
    } catch (err) {
      dispatch(getClimatologyFailed((err as Error).toString()))
      logError(err)
    }
  }
