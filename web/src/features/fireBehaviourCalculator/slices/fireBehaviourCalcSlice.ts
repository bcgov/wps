import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { FBCStation, postFBCStations } from 'api/fbCalcAPI'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FuelTypes } from '../fuelTypes'

interface State {
  loading: boolean
  error: string | null
  fireBehaviourResultStations: FBCStation[]
}

const initialState: State = {
  loading: false,
  error: null,
  fireBehaviourResultStations: []
}

const fireBehaviourStationsSlice = createSlice({
  name: 'fireBehaviourStations',
  initialState,
  reducers: {
    getFireBehaviourStationsStart(state: State) {
      state.error = null
      state.loading = true
      state.fireBehaviourResultStations = []
    },
    getFireBehaviourStationsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireBehaviourStationsSuccess(state: State, action: PayloadAction<FBCStation[]>) {
      state.error = null
      state.fireBehaviourResultStations = action.payload
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
  grassCurePercentage: number | undefined
): AppThunk => async dispatch => {
  const fuelTypeDetails = FuelTypes.lookup(fuelType)
  try {
    dispatch(getFireBehaviourStationsStart())
    const fireBehaviourStations = await postFBCStations(
      date,
      stationCodes,
      fuelTypeDetails.name,
      fuelTypeDetails.percentage_conifer,
      grassCurePercentage,
      fuelTypeDetails.percentage_dead_balsam_fir,
      fuelTypeDetails.crown_base_height
    )
    dispatch(getFireBehaviourStationsSuccess(fireBehaviourStations))
  } catch (err) {
    dispatch(getFireBehaviourStationsFailed(err.toString()))
    logError(err)
  }
}
