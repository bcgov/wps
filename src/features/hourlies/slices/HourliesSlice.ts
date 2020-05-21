import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { HourlyReadings, getHourlies } from 'api/hourliesAPI'
import { AppThunk } from 'app/store'

interface State {
  loading: boolean
  error: string | null
  hourlies: HourlyReadings[]
}

const initialState: State = {
  loading: false,
  error: null,
  hourlies: []
}

const hourlies = createSlice({
  name: 'hourlies',
  initialState,
  reducers: {
    getHourliesStart(state: State) {
      state.loading = true
    },
    getHourliesFailed(state: State, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    getHourliesSuccess(state: State, action: PayloadAction<HourlyReadings[]>) {
      state.loading = false
      state.hourlies = action.payload
    }
  }
})

export const {
  getHourliesStart,
  getHourliesFailed,
  getHourliesSuccess
} = hourlies.actions

export default hourlies.reducer

export const fetchHistoricalReadings = (
  stationCodes: number[]
): AppThunk => async dispatch => {
  try {
    dispatch(getHourliesStart())
    const hourlies = await getHourlies(stationCodes)
    dispatch(getHourliesSuccess(hourlies))
  } catch (err) {
    dispatch(getHourliesFailed(err))
  }
}
