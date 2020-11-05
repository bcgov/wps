import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { Station, getStations } from 'api/stationAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  stations: Station[]
}

const initialState: State = {
  loading: false,
  error: null,
  stations: []
}

const stationsSlice = createSlice({
  name: 'stations',
  initialState,
  reducers: {
    getStationsStart(state: State) {
      state.loading = true
    },
    getStationsFailed(state: State, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    getStationsSuccess(state: State, action: PayloadAction<Station[]>) {
      state.error = null
      state.stations = action.payload
      state.loading = false
    }
  }
})

const { getStationsStart, getStationsFailed, getStationsSuccess } = stationsSlice.actions

export default stationsSlice.reducer

export const fetchWxStations = (): AppThunk => async dispatch => {
  try {
    dispatch(getStationsStart())
    const stations = await getStations()
    dispatch(getStationsSuccess(stations))
  } catch (err) {
    dispatch(getStationsFailed(err.toString()))
    logError(err)
  }
}
