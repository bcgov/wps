import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { Station, getStations } from 'api/stationAPI'
import { AppThunk } from 'app/store'

interface StationsState {
  isLoading: boolean
  error: string | null
  stations: Station[]
}

export const stationsInitialState: StationsState = {
  isLoading: false,
  error: null,
  stations: []
}

const stations = createSlice({
  name: 'stations',
  initialState: stationsInitialState,
  reducers: {
    getStationsStart(state: StationsState) {
      state.isLoading = true
    },
    getStationsError(state: StationsState, action: PayloadAction<string>) {
      state.isLoading = false
      state.error = action.payload
    },
    getStationsSuccess(state: StationsState, action: PayloadAction<Station[]>) {
      state.isLoading = false
      state.stations = action.payload
      state.error = null
    }
  }
})

export const {
  getStationsStart,
  getStationsError,
  getStationsSuccess
} = stations.actions

export default stations.reducer

export const fetchStations = (): AppThunk => async dispatch => {
  try {
    dispatch(getStationsStart())
    const stations = await getStations()
    dispatch(getStationsSuccess(stations))
  } catch (err) {
    dispatch(getStationsError(err.toString()))
  }
}
