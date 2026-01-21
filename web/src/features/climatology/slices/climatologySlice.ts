import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { getClimatology } from 'api/climatologyAPI'
import { AppThunk } from 'app/store'
import {
  AggregationPeriod,
  ClimatologyResponse,
  MultiYearClimatologyResult,
  ReferencePeriod,
  WeatherVariable
} from '../interfaces'
import { logError } from 'utils/error'

export interface ClimatologyState {
  loading: boolean
  error: string | null
  result: ClimatologyResponse | null
  multiYearResult: MultiYearClimatologyResult | null
}

export const climatologyInitialState: ClimatologyState = {
  loading: false,
  error: null,
  result: null,
  multiYearResult: null
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
      state.multiYearResult = null
      state.loading = false
      state.error = null
    },
    getMultiYearClimatologySuccess(
      state: ClimatologyState,
      action: PayloadAction<MultiYearClimatologyResult>
    ) {
      state.multiYearResult = action.payload
      state.result = null
      state.loading = false
      state.error = null
    },
    getClimatologyFailed(state: ClimatologyState, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    resetClimatologyResult(state: ClimatologyState) {
      state.result = null
      state.multiYearResult = null
      state.error = null
    }
  }
})

export const {
  getClimatologyStart,
  getClimatologyFailed,
  getClimatologySuccess,
  getMultiYearClimatologySuccess,
  resetClimatologyResult
} = climatologySlice.actions

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

export const fetchMultiYearClimatology =
  (
    stationCode: number,
    variable: WeatherVariable,
    aggregation: AggregationPeriod,
    referencePeriod: ReferencePeriod,
    comparisonYears: number[]
  ): AppThunk =>
  async dispatch => {
    try {
      dispatch(getClimatologyStart())

      // Fetch data for all comparison years in parallel
      const promises = comparisonYears.map(year =>
        getClimatology(stationCode, variable, aggregation, referencePeriod, year)
      )

      const results = await Promise.all(promises)

      // Use the first result for climatology base data
      const baseResult = results[0]

      // Merge all year data
      const multiYearResult: MultiYearClimatologyResult = {
        climatology: baseResult.climatology,
        years_data: results.map((r, idx) => ({
          year: comparisonYears[idx],
          data: r.comparison_year_data
        })),
        station: baseResult.station,
        variable: baseResult.variable,
        aggregation: baseResult.aggregation,
        reference_period: baseResult.reference_period,
        comparison_years: comparisonYears
      }

      dispatch(getMultiYearClimatologySuccess(multiYearResult))
    } catch (err) {
      dispatch(getClimatologyFailed((err as Error).toString()))
      logError(err)
    }
  }
