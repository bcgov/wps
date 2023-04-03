import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { ModelType, ObservedDaily, getObservedDailies } from 'api/moreCast2API'
import { StationGroupMember } from 'api/stationAPI'
import { AppThunk } from 'app/store'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'
import { parseObservedDailiesFromResponse } from 'features/moreCast2/util'
import { fillInTheYesterdayDailyBlanks } from 'features/moreCast2/yesterdayDailies'
import { logError } from 'utils/error'

export interface ColYesterdayDailies {
  colField: keyof MoreCast2ForecastRow
  modelType: ModelType
  yesterdayDailies: ObservedDaily[]
}

interface State {
  loading: boolean
  error: string | null
  colYesterdayDailies: ColYesterdayDailies | null
}

export const initialState: State = {
  loading: false,
  error: null,
  colYesterdayDailies: null
}

const columnYesterdaySlice = createSlice({
  name: 'ColumnYesterdaySlice',
  initialState,
  reducers: {
    getColumnYesterdayDailiesStart(state: State) {
      state.error = null
      state.loading = true
    },
    getColumnYesterdayDailiesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getColumnYesterdayDailiesSuccess(state: State, action: PayloadAction<ColYesterdayDailies>) {
      state.error = null
      state.colYesterdayDailies = action.payload
      state.loading = false
    }
  }
})

export const { getColumnYesterdayDailiesStart, getColumnYesterdayDailiesFailed, getColumnYesterdayDailiesSuccess } =
  columnYesterdaySlice.actions

export default columnYesterdaySlice.reducer

export const getColumnYesterdayDailies =
  (
    stationCodes: number[],
    fireCentreStations: StationGroupMember[],
    dateInterval: string[],
    model: ModelType,
    colField: keyof MoreCast2ForecastRow,
    fromDate: string,
    toDate: string
  ): AppThunk =>
  async dispatch => {
    try {
      dispatch(getColumnYesterdayDailiesStart())
      let observedDailies: ObservedDaily[] = []
      if (stationCodes.length) {
        const observedDailiesResponse = await getObservedDailies(stationCodes, fromDate, toDate)
        const dailies: ObservedDaily[] = parseObservedDailiesFromResponse(observedDailiesResponse)
        observedDailies = fillInTheYesterdayDailyBlanks(fireCentreStations, dailies, dateInterval)
      }
      dispatch(
        getColumnYesterdayDailiesSuccess({
          colField: colField,
          modelType: model,
          yesterdayDailies: observedDailies
        })
      )
    } catch (err) {
      dispatch(getColumnYesterdayDailiesFailed((err as Error).toString()))
      logError(err)
    }
  }
