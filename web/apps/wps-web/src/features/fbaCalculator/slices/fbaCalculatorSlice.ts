import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import { type FBAStation, type FBAWeatherStationsResponse, postFBAStations } from '@wps/api/fbaCalcAPI'
import { PST_UTC_OFFSET } from '@wps/utils/constants'
import { pstFormatter } from '@wps/utils/date'
import { logError } from '@wps/utils/error'
import type { AppThunk } from 'app/store'
import type { FBATableRow } from 'features/fbaCalculator/RowManager'
import { isEmpty, isNil } from 'lodash'
import { DateTime } from 'luxon'
import { FuelTypes } from '../fuelTypes'

export interface FBACalcState {
  loading: boolean
  error: string | null
  fireBehaviourResultStations: FBAStation[]
  date: string | null
}

const initialState: FBACalcState = {
  loading: false,
  error: null,
  fireBehaviourResultStations: [],
  date: null
}

const fireBehaviourStationsSlice = createSlice({
  name: 'fireBehaviourStations',
  initialState,
  reducers: {
    getFireBehaviourStationsStart(state: FBACalcState) {
      state.error = null
      state.loading = true
      state.fireBehaviourResultStations = []
      state.date = null
    },
    getFireBehaviourStationsFailed(state: FBACalcState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireBehaviourStationsSuccess(state: FBACalcState, action: PayloadAction<FBAWeatherStationsResponse>) {
      state.error = null
      state.fireBehaviourResultStations = action.payload.stations
      state.date = DateTime.fromFormat(action.payload.date, 'yyyy/MM/dd')
        .startOf('day')
        .setZone(`UTC${PST_UTC_OFFSET}`)
        .toISO()
      state.loading = false
    }
  }
})

export const { getFireBehaviourStationsStart, getFireBehaviourStationsFailed, getFireBehaviourStationsSuccess } =
  fireBehaviourStationsSlice.actions

export default fireBehaviourStationsSlice.reducer

export const fetchFireBehaviourStations =
  (date: DateTime, fbcInputRows: FBATableRow[]): AppThunk =>
  async dispatch => {
    const fetchableFireStations = fbcInputRows.flatMap(row => {
      const fuelTypeDetails = FuelTypes.lookup(row.fuelType?.value)
      if (isNil(fuelTypeDetails) || isNil(row.weatherStation)) {
        return []
      }
      return {
        id: row.id,
        stationCode: parseInt(row.weatherStation ? row.weatherStation.value : '', 10),
        fuelType: fuelTypeDetails.name,
        percentageConifer: fuelTypeDetails.percentage_conifer,
        grassCurePercentage: row.grassCure,
        percentageDeadBalsamFir: fuelTypeDetails.percentage_dead_balsam_fir,
        crownBaseHeight: fuelTypeDetails.crown_base_height,
        windSpeed: row.windSpeed,
        precip: row.precip
      }
    })
    try {
      if (!isEmpty(fetchableFireStations)) {
        dispatch(getFireBehaviourStationsStart())
        const fireBehaviourStations = await postFBAStations(pstFormatter(date), fetchableFireStations)
        dispatch(getFireBehaviourStationsSuccess(fireBehaviourStations))
      }
    } catch (err) {
      dispatch(getFireBehaviourStationsFailed((err as Error).toString()))
      logError(err)
    }
  }
