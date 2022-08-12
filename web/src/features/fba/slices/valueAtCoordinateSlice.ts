import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getValueAtCoordinate } from 'api/fbaAPI'

interface State {
  loading: boolean
  error: string | null
  valueAtCoordinate: number | undefined
}

const initialState: State = {
  loading: false,
  error: null,
  valueAtCoordinate: undefined
}

const valueAtCoordinateSlice = createSlice({
  name: 'valueAtCoordinate',
  initialState,
  reducers: {
    getValueAtCoordinateStart(state: State) {
      state.error = null
      state.loading = true
      state.valueAtCoordinate = undefined
    },
    getValueAtCoordinateFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getValueAtCoordinateSuccess(state: State, action: PayloadAction<number>) {
      state.error = null
      state.valueAtCoordinate = action.payload
      state.loading = false
    }
  }
})

export const { getValueAtCoordinateStart, getValueAtCoordinateFailed, getValueAtCoordinateSuccess } =
  valueAtCoordinateSlice.actions

export default valueAtCoordinateSlice.reducer

export const fetchValueAtCoordinate =
  (layer: string, latitude: number, longitude: number): AppThunk =>
  async dispatch => {
    try {
      dispatch(getValueAtCoordinateStart())
      const value = await getValueAtCoordinate(layer, latitude, longitude)
      dispatch(getValueAtCoordinateSuccess(value))
    } catch (err) {
      dispatch(getValueAtCoordinateFailed((err as Error).toString()))
      logError(err)
    }
  }
