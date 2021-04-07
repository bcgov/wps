import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { Station } from 'api/stationAPI'

interface State {
  loading: boolean
  error: string | null
  stations: Station[]
  stationsByCode: Record<number, Station | undefined>
}

const initialState: State = {
  loading: false,
  error: null,
  stations: [],
  stationsByCode: {}
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
      const stationsByCode: State['stationsByCode'] = {}
      action.payload.forEach(station => {
        stationsByCode[station.code] = station
      })
      state.stationsByCode = stationsByCode
      state.loading = false
    }
  }
})

export const {
  getStationsStart,
  getStationsFailed,
  getStationsSuccess
} = stationsSlice.actions

export default stationsSlice.reducer
