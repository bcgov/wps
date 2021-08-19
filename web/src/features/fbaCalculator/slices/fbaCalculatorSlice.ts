import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { FBAStation, FBAWeatherStationsResponse, postFBAStations } from 'api/fbaCalcAPI'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FBAInputRow } from 'features/fbaCalculator/components/FBAInputGrid'
import { FuelTypes } from '../fuelTypes'
import { isEmpty, isEqual, isNull, isUndefined } from 'lodash'

interface State {
  loading: boolean
  error: string | null
  fireBehaviourResultStations: FBAStation[]
  date: string | null
}

const initialState: State = {
  loading: false,
  error: null,
  fireBehaviourResultStations: [],
  date: null
}

const fireBehaviourStationsSlice = createSlice({
  name: 'fireBehaviourStations',
  initialState,
  reducers: {
    getFireBehaviourStationsStart(state: State) {
      state.error = null
      state.loading = true
      state.fireBehaviourResultStations = []
      state.date = null
    },
    getFireBehaviourStationsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireBehaviourStationsSuccess(
      state: State,
      action: PayloadAction<FBAWeatherStationsResponse>
    ) {
      state.error = null
      state.fireBehaviourResultStations = action.payload.stations
      state.date = action.payload.date
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
      const fireBehaviourStations = await postFBAStations(date, fetchableFireStations)
      dispatch(getFireBehaviourStationsSuccess(fireBehaviourStations))
    }
  } catch (err) {
    dispatch(getFireBehaviourStationsFailed(err.toString()))
    logError(err)
  }
}
