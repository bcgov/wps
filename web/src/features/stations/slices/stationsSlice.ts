import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { StationSource, DetailedGeoJsonStation, GeoJsonStation } from 'api/stationAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
interface State {
  loading: boolean
  error: string | null
  stations: GeoJsonStation[] | DetailedGeoJsonStation[]
  stationsByCode: Record<number, GeoJsonStation | DetailedGeoJsonStation | undefined>
  selectedStationsByCode: number[]
  codesOfRetrievedStationData: number[]
}

const initialState: State = {
  loading: false,
  error: null,
  stations: [],
  stationsByCode: {},
  selectedStationsByCode: [],
  codesOfRetrievedStationData: []
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
    },
    selectStation(state: State, action: PayloadAction<number>) {
      const selectedStationsList = state.selectedStationsByCode
      selectedStationsList.push(action.payload)
      const selectedStationsSet = new Set(selectedStationsList)
      state.selectedStationsByCode = Array.from(selectedStationsSet.values())
    },
    selectStations(state: State, action: PayloadAction<number[]>) {
      state.selectedStationsByCode = []
      state.selectedStationsByCode = action.payload
    }
  }
})

export const fetchWxStations = (
  stationGetter:
    | ((source: StationSource) => Promise<GeoJsonStation[]>)
    | ((source: StationSource) => Promise<DetailedGeoJsonStation[]>),
  source: StationSource = StationSource.unspecified
): AppThunk => async dispatch => {
  try {
    dispatch(getStationsStart())
    const stations = await stationGetter(source)
    dispatch(getStationsSuccess(stations))
  } catch (err) {
    dispatch(getStationsFailed(err.toString()))
    logError(err)
  }
}

export const {
  getStationsStart,
  getStationsFailed,
  getStationsSuccess,
  selectStation,
  selectStations
} = stationsSlice.actions

export default stationsSlice.reducer
