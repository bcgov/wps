import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { Station, getStations } from 'api/stationAPI'
import { AppThunk } from 'app/store'

interface StationsState {
  loading: boolean
  error: string | null
  stations: Station[]
}

export const initialState: StationsState = {
  loading: false,
  error: null,
  stations: []
}

const stationsSlice = createSlice({
  name: 'stations',
  initialState: initialState,
  reducers: {
    getStationsStart(state: StationsState) {
      state.loading = true
    },
    getStationsFailed(state: StationsState, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    getStationsSuccess(state: StationsState, action: PayloadAction<Station[]>) {
      state.loading = false
      state.stations = action.payload
      state.error = null
    }
  }
})

export const {
  getStationsStart,
  getStationsFailed,
  getStationsSuccess
} = stationsSlice.actions

export default stationsSlice.reducer

export const fetchWxStations = (): AppThunk => async dispatch => {
  try {
    dispatch(getStationsStart())
    const stations = await getStations()
    dispatch(getStationsSuccess(stations))
  } catch (err) {
    dispatch(getStationsFailed(err))
  }
}
