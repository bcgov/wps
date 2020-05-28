import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { Reading, ReadingValue, getReadings } from 'api/readingAPI'
import { AppThunk } from 'app/store'

interface State {
  loading: boolean
  error: string | null
  readingsByStation: Record<number, ReadingValue[] | undefined>
  readings: Reading[]
}

const initialState: State = {
  loading: false,
  error: null,
  readingsByStation: {},
  readings: []
}

const readingsSlice = createSlice({
  name: 'readings',
  initialState,
  reducers: {
    getReadingsStart(state: State) {
      state.loading = true
    },
    getReadingsFailed(state: State, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    getReadingsSuccess(state: State, action: PayloadAction<Reading[]>) {
      state.loading = false
      state.error = null
      state.readings = action.payload
      action.payload.forEach(reading => {
        if (reading.station) {
          state.readingsByStation[reading.station.code] = reading.values
        }
      })
    }
  }
})

export const {
  getReadingsStart,
  getReadingsFailed,
  getReadingsSuccess
} = readingsSlice.actions

export default readingsSlice.reducer

export const fetchReadings = (stationCodes: number[]): AppThunk => async dispatch => {
  try {
    dispatch(getReadingsStart())
    const readings = await getReadings(stationCodes)
    dispatch(getReadingsSuccess(readings))
  } catch (err) {
    dispatch(getReadingsFailed(err))
  }
}
