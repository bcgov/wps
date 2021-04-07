import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { Station, getStations } from 'api/stationAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

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
  name: 'fireWeatherStations',
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
