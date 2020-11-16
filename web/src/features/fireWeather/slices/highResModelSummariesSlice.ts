import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { ModelSummary, ModelSummariesForStation, getModelSummaries } from 'api/modelAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  highResModelSummariesByStation: Record<number, ModelSummary[] | undefined>
}

const initialState: State = {
  loading: false,
  error: null,
  highResModelSummariesByStation: {}
}

const highResModelSummariesSlice = createSlice({
  name: 'highResModelSummaries',
  initialState,
  reducers: {
    getHighResModelSummariesStart(state: State) {
      state.error = null
      state.loading = true
    },
    getHighResModelSummariesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getHighResModelSummariesSuccess(
      state: State,
      action: PayloadAction<ModelSummariesForStation[]>
    ) {
      state.error = null
      action.payload.forEach(summary => {
        if (summary.station) {
          const code = summary.station.code
          state.highResModelSummariesByStation[code] = summary.values
        }
      })
      state.loading = false
    }
  }
})

export const {
  getHighResModelSummariesStart,
  getHighResModelSummariesFailed,
  getHighResModelSummariesSuccess
} = highResModelSummariesSlice.actions

export default highResModelSummariesSlice.reducer

export const fetchHighResModelSummaries = (
  stationCodes: number[]
): AppThunk => async dispatch => {
  try {
    dispatch(getHighResModelSummariesStart())
    const summaries = await getModelSummaries(stationCodes, 'HRDPS')
    dispatch(getHighResModelSummariesSuccess(summaries))
  } catch (err) {
    dispatch(getHighResModelSummariesFailed(err.toString()))
    logError(err)
  }
}
