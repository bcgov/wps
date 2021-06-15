import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { WeatherStation, PlanningArea, FireCentre, getHFIStations, HFIWeatherStationsResponse } from 'api/hfiCalcAPI'
import { AppThunk } from 'app/store'
import { logError } from 'utils/error'

interface State {
  loading: boolean
  error: string | null
  weatherStations: WeatherStation[]
  fireCentres: FireCentre[]
  planningAreasByFireCentre: Record<string, PlanningArea[] | undefined>
  stationsByPlanningArea: Record<string, WeatherStation[] | undefined>
}

const initialState: State = {
  loading: false,
  error: null,
  weatherStations: [],
  fireCentres: [],
  planningAreasByFireCentre: {},
  stationsByPlanningArea: {}
}

const stationsSlice = createSlice({
  name: 'hfiStations',
  initialState,
  reducers: {
    getHFIStationsStart(state: State) {
      state.error = null
      state.loading = true
      state.fireCentres = []
      state.planningAreasByFireCentre = {}
      state.stationsByPlanningArea = {}
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
      state.planningAreasByFireCentre = action.payload.planning_areas_by_fire_centre
      state.stationsByPlanningArea = action.payload.stations_by_planning_area
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
