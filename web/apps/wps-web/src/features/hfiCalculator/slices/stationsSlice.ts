import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

import { type FireCentre, getHFIStations, type HFIWeatherStationsResponse } from '@wps/api/hfiCalculatorAPI'
import { logError } from '@wps/utils/error'
import type { AppThunk } from 'app/store'

export interface StationsState {
  loading: boolean
  error: string | null
  fireCentres: FireCentre[]
}

const initialState: StationsState = {
  loading: false,
  error: null,
  fireCentres: []
}

const stationsSlice = createSlice({
  name: 'hfiStations',
  initialState,
  reducers: {
    getHFIStationsStart(state: StationsState) {
      state.error = null
      state.loading = true
      state.fireCentres = []
    },
    getHFIStationsFailed(state: StationsState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getHFIStationsSuccess(state: StationsState, action: PayloadAction<HFIWeatherStationsResponse>) {
      state.error = null
      state.fireCentres = action.payload.fire_centres
      state.loading = false
    }
  }
})

export const { getHFIStationsStart, getHFIStationsFailed, getHFIStationsSuccess } = stationsSlice.actions

export default stationsSlice.reducer

export const fetchHFIStations = (): AppThunk => async dispatch => {
  try {
    dispatch(getHFIStationsStart())
    const hfiStations = await getHFIStations()
    dispatch(getHFIStationsSuccess(hfiStations))
  } catch (err) {
    dispatch(getHFIStationsFailed((err as Error).toString()))
    logError(err)
  }
}
