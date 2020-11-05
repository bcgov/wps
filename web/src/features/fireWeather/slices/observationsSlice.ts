import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { Observation, ObservedValue, getObservations } from 'api/observationAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  observationsByStation: Record<number, ObservedValue[] | undefined>
  observations: Observation[]
}

const initialState: State = {
  loading: false,
  error: null,
  observationsByStation: {},
  observations: []
}

const observationsSlice = createSlice({
  name: 'observations',
  initialState,
  reducers: {
    getObservationsStart(state: State) {
      state.error = null
      state.loading = true
    },
    getObservationsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getObservationsSuccess(state: State, action: PayloadAction<Observation[]>) {
      state.error = null
      state.observations = action.payload
      action.payload.forEach(observed => {
        if (observed.station) {
          state.observationsByStation[observed.station.code] = observed.values
        }
      })
      state.loading = false
    }
  }
})

export const {
  getObservationsStart,
  getObservationsFailed,
  getObservationsSuccess
} = observationsSlice.actions

export default observationsSlice.reducer

export const fetchObservations = (stationCodes: number[]): AppThunk => async dispatch => {
  try {
    dispatch(getObservationsStart())
    const observations = await getObservations(stationCodes)
    dispatch(getObservationsSuccess(observations))
  } catch (err) {
    dispatch(getObservationsFailed(err.toString()))
    logError(err)
  }
}
