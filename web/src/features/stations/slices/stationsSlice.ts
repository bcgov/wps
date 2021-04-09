import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { GeoJsonStation } from 'api/stationAPI'

interface State {
  loading: boolean
  error: string | null
  stations: GeoJsonStation[]
  stationsByCode: Record<number, GeoJsonStation | undefined>
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
    getStationsSuccess(state: State, action: PayloadAction<GeoJsonStation[]>) {
      state.error = null
      state.stations = action.payload
      const stationsByCode: State['stationsByCode'] = {}
      action.payload.forEach(station => {
        stationsByCode[station.properties.code] = station
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
