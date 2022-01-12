import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import {
  FBAWeatherStationsResponse,
  postFBAStations,
  postHistoricFBAStations,
  WeatherWarningStation
} from 'api/fbaCalcAPI'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { isEmpty, isEqual, isNull, isUndefined } from 'lodash'
import { FBATableRow } from 'features/fbaCalculator/RowManager'
import { DateTime } from 'luxon'
import { PST_UTC_OFFSET } from 'utils/constants'
import { FuelTypes } from '../fuelTypes'

interface State {
  loading: boolean
  error: string | null
  fireBehaviourResultStations: WeatherWarningStation | null
}

const initialState: State = {
  loading: false,
  error: null,
  fireBehaviourResultStations: null
}

const weatherWarningSlice = createSlice({
  name: 'weatherWarningStations',
  initialState,
  reducers: {
    getWeatherWarningStationsStart(state: State) {
      state.error = null
      state.loading = true
      state.fireBehaviourResultStations = null
    },
    getWeatherWarningStationsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getWeatherWarningStationsSuccess(
      state: State,
      action: PayloadAction<WeatherWarningStation>
    ) {
      state.error = null
      state.fireBehaviourResultStations = action.payload
      state.loading = false
    }
  }
})

export const {
  getWeatherWarningStationsStart,
  getWeatherWarningStationsFailed,
  getWeatherWarningStationsSuccess
} = weatherWarningSlice.actions

export default weatherWarningSlice.reducer

export const fetchWeatherWarningStations =
  (date: string, fbcInputRows: FBATableRow[]): AppThunk =>
  async dispatch => {
    const fetchableFireStations = fbcInputRows.flatMap(row => {
      if (isUndefined(row.weatherStation) || isEqual(row.weatherStation, 'undefined')) {
        return []
      }
      const fuelTypeDetails = FuelTypes.lookup(row.fuelType?.value)

      return {
        id: row.id,
        dailies: [],
        fuelType: fuelTypeDetails?.name,
        station_code: parseInt(row.weatherStation ? row.weatherStation.value : ''),
        duff_moisture_code: parseInt(row.weatherStation ? row.weatherStation.value : ''),
        build_up_index: parseInt(row.weatherStation ? row.weatherStation.value : '')
      }
    })
    try {
      if (!isEmpty(fetchableFireStations)) {
        dispatch(getWeatherWarningStationsStart())
        const fireBehaviourStations = await postHistoricFBAStations(
          date,
          fetchableFireStations
        )
        dispatch(getWeatherWarningStationsSuccess(fireBehaviourStations))
      }
    } catch (err) {
      dispatch(getWeatherWarningStationsFailed((err as Error).toString()))
      logError(err)
    }
  }
