import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getValueAtCoordinate } from 'api/fbaAPI'
import { DateTime } from 'luxon'

export interface IValueAtCoordinate {
  value: number
  date: DateTime
  description: string
}
interface State {
  loading: boolean
  error: string | null
  values: IValueAtCoordinate[]
}

const initialState: State = {
  loading: false,
  error: null,
  values: []
}

const valueAtCoordinateSlice = createSlice({
  name: 'valueAtCoordinate',
  initialState,
  reducers: {
    getValueAtCoordinateStart(state: State) {
      state.error = null
      state.loading = true
      state.values = []
    },
    getValueAtCoordinateFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getValueAtCoordinateSuccess(state: State, action: PayloadAction<IValueAtCoordinate>) {
      state.error = null
      state.values.push(action.payload)
      state.loading = false
    }
  }
})

export const { getValueAtCoordinateStart, getValueAtCoordinateFailed, getValueAtCoordinateSuccess } =
  valueAtCoordinateSlice.actions

export default valueAtCoordinateSlice.reducer

export const fetchValueAtCoordinate =
  (layers: string[], latitude: number, longitude: number, description: string, date: DateTime): AppThunk =>
  async dispatch => {
    try {
      dispatch(getValueAtCoordinateStart())
      // Only fetching the one right now...
      const value = await getValueAtCoordinate(layers[0], latitude, longitude)
      dispatch(getValueAtCoordinateSuccess({ value: value, date: date, description: description }))
    } catch (err) {
      dispatch(getValueAtCoordinateFailed((err as Error).toString()))
      logError(err)
    }
  }
