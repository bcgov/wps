import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import axios from 'api/axios'
import { AppThunk } from 'app/store'

export interface RepresentativeStationState {
  loading: boolean
  error: string | null
  repStations: FireShapeStation[]
}

const initialState: RepresentativeStationState = {
  loading: false,
  error: null,
  repStations: []
}

export interface FireShapeStation {
  fire_number: string
  station_code: number
}

export interface FireShapeStations {
  representative_stations: FireShapeStation[]
}

export async function getRepStations(): Promise<FireShapeStations> {
  const url = '/risk-map/weather'
  const { data } = await axios.post(url)
  return data
}

const representativeStationSlice = createSlice({
  name: 'repStationsSlice',
  initialState,
  reducers: {
    getRepStationStart(state: RepresentativeStationState) {
      state.error = null
      state.loading = true
      state.repStations = []
    },
    getRepStationFailed(state: RepresentativeStationState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getRepStationSuccess(state: RepresentativeStationState, action: PayloadAction<FireShapeStation[]>) {
      state.error = null
      state.repStations = action.payload
      state.loading = false
    }
  }
})

export const { getRepStationStart, getRepStationFailed, getRepStationSuccess } = representativeStationSlice.actions

export default representativeStationSlice.reducer

export const fetchRepresentativeStations = (): AppThunk => async dispatch => {
  try {
    dispatch(getRepStationStart())
    const repStationsData = await getRepStations()
    dispatch(getRepStationSuccess(repStationsData.representative_stations))
  } catch (err) {
    dispatch(getRepStationFailed((err as Error).toString()))
  }
}
