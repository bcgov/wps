import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { FBCStation, postFBCStations } from 'api/fbCalcAPI'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  fireBehaviourStations: FBCStation[]
}

const initialState: State = {
  loading: false,
  error: null,
  fireBehaviourStations: []
}

const fireBehaviourStationsSlice = createSlice({
  name: 'fireBehaviourStations',
  initialState,
  reducers: {
    getFireBehaviourStationsStart(state: State) {
      state.error = null
      state.loading = true
      state.fireBehaviourStations = []
    },
    getFireBehaviourStationsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireBehaviourStationsSuccess(state: State, action: PayloadAction<FBCStation[]>) {
      state.error = null
      state.fireBehaviourStations = action.payload
      state.loading = false
    }
  }
})

export const {
  getFireBehaviourStationsStart,
  getFireBehaviourStationsFailed,
  getFireBehaviourStationsSuccess
} = fireBehaviourStationsSlice.actions

export default fireBehaviourStationsSlice.reducer

export const fetchFireBehaviourStations = (
  date: string,
  stationCodes: number[],
  fuelType: string,
  percentageConifer: number,
  grassCurePercentage: number,
  crownBurnHeight: number
): AppThunk => async dispatch => {
  try {
    dispatch(getFireBehaviourStationsStart())
    const fireBehaviourStations = await postFBCStations(
      date,
      stationCodes,
      fuelType,
      percentageConifer,
      grassCurePercentage,
      crownBurnHeight
    )
    dispatch(getFireBehaviourStationsSuccess(fireBehaviourStations))
  } catch (err) {
    dispatch(getFireBehaviourStationsFailed(err.toString()))
    logError(err)
  }
}
