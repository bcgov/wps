import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { StationSource, DetailedGeoJsonStation, GeoJsonStation } from 'api/stationAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
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
    getStationsSuccess(
      state: State,
      action: PayloadAction<GeoJsonStation[] | DetailedGeoJsonStation[]>
    ) {
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

export const fetchWxStations = (
  stationGetter:
    | ((source: StationSource) => Promise<GeoJsonStation[]>)
    | ((source: StationSource) => Promise<DetailedGeoJsonStation[]>)
): AppThunk => async dispatch => {
  try {
    dispatch(getStationsStart())
    const stations = await stationGetter(StationSource.local_storage)
    dispatch(getStationsSuccess(stations))
  } catch (err) {
    dispatch(getStationsFailed(err.toString()))
    logError(err)
  }
}

export const {
  getStationsStart,
  getStationsFailed,
  getStationsSuccess
} = stationsSlice.actions

export default stationsSlice.reducer
