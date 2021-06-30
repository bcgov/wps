import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getDailies, StationDaily } from 'api/hfiCalculatorAPI'

interface State {
  loading: boolean
  error: string | null
  dailies: StationDaily[]
}

const initialState: State = {
  loading: false,
  error: null,
  dailies: []
}

const dailiesSlice = createSlice({
  name: 'dailies',
  initialState,
  reducers: {
    getDailiesStart(state: State) {
      state.error = null
      state.loading = true
      state.dailies = []
    },
    getDailiesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getDailiesSuccess(state: State, action: PayloadAction<StationDaily[]>) {
      state.error = null
      state.dailies = action.payload
      state.loading = false
    }
  }
})

export const {
  getDailiesStart,
  getDailiesFailed,
  getDailiesSuccess
} = dailiesSlice.actions

export default dailiesSlice.reducer

export const fetchHFIDailies = (
  startTime: number,
  endTime: number
): AppThunk => async dispatch => {
  try {
    dispatch(getDailiesStart())
    const dailies = await getDailies(startTime, endTime)
    dispatch(getDailiesSuccess(dailies))
  } catch (err) {
    dispatch(getDailiesFailed(err.toString()))
    logError(err)
  }
}
