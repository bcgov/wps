import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { FBCStation, postFBCStations } from 'api/fbCalcAPI'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FBAInputRow } from 'features/fbaCalculator/components/FBAInputGrid'
import { FuelTypes } from '../fuelTypes'
import { isEmpty, isEqual, isNull, isUndefined } from 'lodash'

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
  fbcInputRows: FBAInputRow[]
): AppThunk => async dispatch => {
  const fetchableFireStations = fbcInputRows.flatMap(row => {
    const fuelTypeDetails = FuelTypes.lookup(row.fuelType)
    if (
      isNull(fuelTypeDetails) ||
      isUndefined(fuelTypeDetails) ||
      isUndefined(row.weatherStation) ||
      isEqual(row.weatherStation, 'undefined')
    ) {
      return []
    }
    return {
      date,
      stationCode: parseInt(row.weatherStation),
      fuelType: fuelTypeDetails.name,
      percentageConifer: fuelTypeDetails.percentage_conifer,
      grassCurePercentage: row.grassCure,
      percentageDeadBalsamFir: fuelTypeDetails.percentage_dead_balsam_fir,
      crownBaseHeight: fuelTypeDetails.crown_base_height,
      windSpeed: row.windSpeed
    }
  })
  try {
    if (!isEmpty(fetchableFireStations)) {
      dispatch(getFireBehaviourStationsStart())
      const fireBehaviourStations = await postFBCStations(fetchableFireStations)
      dispatch(getFireBehaviourStationsSuccess(fireBehaviourStations))
    }
  } catch (err) {
    dispatch(getFireBehaviourStationsFailed(err.toString()))
    logError(err)
  }
}
