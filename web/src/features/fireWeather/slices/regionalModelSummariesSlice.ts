import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { ModelSummary, ModelSummariesForStation, getModelSummaries } from 'api/modelAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  regionalModelSummariesByStation: Record<number, ModelSummary[] | undefined>
}

const initialState: State = {
  loading: false,
  error: null,
  regionalModelSummariesByStation: {}
}

const regionalModelSummariesSlice = createSlice({
  name: 'regionalModelSummaries',
  initialState,
  reducers: {
    getRegionalModelSummariesStart(state: State) {
      state.error = null
      state.loading = true
      state.regionalModelSummariesByStation = {}
    },
    getRegionalModelSummariesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getRegionalModelSummariesSuccess(
      state: State,
      action: PayloadAction<ModelSummariesForStation[]>
    ) {
      state.error = null
      action.payload.forEach(summary => {
        if (summary.station) {
          const code = summary.station.code
          state.regionalModelSummariesByStation[code] = summary.values
        }
      })
      state.loading = false
    }
  }
})

export const {
  getRegionalModelSummariesStart,
  getRegionalModelSummariesFailed,
  getRegionalModelSummariesSuccess
} = regionalModelSummariesSlice.actions

export default regionalModelSummariesSlice.reducer

export const fetchRegionalModelSummaries = (
  stationCodes: number[],
  timeOfInterest: string
): AppThunk => async dispatch => {
  try {
    dispatch(getRegionalModelSummariesStart())
    const summaries = await getModelSummaries(stationCodes, 'RDPS', timeOfInterest)
    dispatch(getRegionalModelSummariesSuccess(summaries))
  } catch (err) {
    dispatch(getRegionalModelSummariesFailed(err.toString()))
    logError(err)
  }
}
