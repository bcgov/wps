import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { FireCentre, getHFIStations, HFIWeatherStationsResponse } from 'api/hfiCalcAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  fireCentres: Record<string, FireCentre>
}

const initialState: State = {
  loading: false,
  error: null,
  fireCentres: {}
}

const stationsSlice = createSlice({
  name: 'hfiStations',
  initialState,
  reducers: {
    getHFIStationsStart(state: State) {
      state.error = null
      state.loading = true
      state.fireCentres = {}
    },
    getHFIStationsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getHFIStationsSuccess(
      state: State,
      action: PayloadAction<HFIWeatherStationsResponse>
    ) {
      state.error = null
      state.fireCentres = action.payload.fire_centres
      state.loading = false
    }
  }
})

export const {
  getHFIStationsStart,
  getHFIStationsFailed,
  getHFIStationsSuccess
} = stationsSlice.actions

export default stationsSlice.reducer

export const fetchHFIStations = (): AppThunk => async dispatch => {
  try {
    dispatch(getHFIStationsStart())
    const hfiStations = await getHFIStations()
    dispatch(getHFIStationsSuccess(hfiStations))
  } catch (err) {
    dispatch(getHFIStationsFailed(err.toString()))
    logError(err)
  }
}
