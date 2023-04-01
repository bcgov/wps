import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { getYesterdayDailies, ObservedDaily } from 'api/moreCast2API'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { parseYesterdayDailiesFromResponse } from 'features/moreCast2/yesterdayDailies'

interface State {
  loading: boolean
  error: string | null
  yesterdayDailies: ObservedDaily[]
}

export const initialState: State = {
  loading: false,
  error: null,
  yesterdayDailies: []
}

const yesterdayDailiesSlice = createSlice({
  name: 'YesterdayDailiesSlice',
  initialState,
  reducers: {
    getYesterdayDailiesStart(state: State) {
      state.error = null
      state.loading = true
    },
    getYesterdayDailiesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getYesterdayDailiesSuccess(state: State, action: PayloadAction<ObservedDaily[]>) {
      state.error = null
      state.yesterdayDailies = action.payload
      state.loading = false
    }
  }
})

export const { getYesterdayDailiesStart, getYesterdayDailiesFailed, getYesterdayDailiesSuccess } =
  yesterdayDailiesSlice.actions

export default yesterdayDailiesSlice.reducer

export const getYesterdayStationDailies =
  (stationCodes: number[], fromDate: string): AppThunk =>
  async dispatch => {
    try {
      if (stationCodes.length) {
        dispatch(getYesterdayDailiesStart())
        const yesterdayDailiesResponse = await getYesterdayDailies(stationCodes, fromDate)
        const yesterdayDailies: ObservedDaily[] = parseYesterdayDailiesFromResponse(yesterdayDailiesResponse)
        dispatch(getYesterdayDailiesSuccess(yesterdayDailies))
      }
    } catch (err) {
      dispatch(getYesterdayDailiesFailed((err as Error).toString()))
      logError(err)
    }
  }
