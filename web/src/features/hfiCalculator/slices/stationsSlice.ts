import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { WeatherStation, PlanningArea, FireCentre, getHFIStations } from 'api/hfiCalcAPI'
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
      state.weatherStations = []
      state.fireCentres = []
      state.planningAreasByFireCentre = {}
      state.stationsByPlanningArea = {}
    },
    getHFIStationsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getHFIStationsSuccess(state: State, action: PayloadAction<WeatherStation[]>) {
      state.error = null
      state.weatherStations = action.payload
      action.payload.forEach(station => {
        // if the station's fire centre isn't already in state.fireCentres array, add it
        if (
          state.fireCentres.find(
            fc => fc.name === station.planning_area.fire_centre.name
          ) === undefined
        ) {
          state.fireCentres.push(station.planning_area.fire_centre)
        }
        // if the fire centre has no planning areas assigned to it yet, create a new array
        // with the station's planning area as the first element in the new array
        if (
          state.planningAreasByFireCentre[station.planning_area.fire_centre.name] ===
          undefined
        ) {
          state.planningAreasByFireCentre[station.planning_area.fire_centre.name] = [
            station.planning_area
          ]
        } else {
          // else if there's already 1+ planning areas assigned to the fire centre, but this station's planning area isn't in the array yet,
          // add it to the fire centre's array
          if (
            state.planningAreasByFireCentre[station.planning_area.fire_centre.name]?.find(
              pa => pa.name === station.planning_area.name
            ) === undefined
          ) {
            state.planningAreasByFireCentre[station.planning_area.fire_centre.name]?.push(
              station.planning_area
            )
          }
        }
        // if there are no stations assigned to the planning area yet, create a new array
        // with the station as the first element in the new array
        if (state.stationsByPlanningArea[station.planning_area.name] === undefined) {
          state.stationsByPlanningArea[station.planning_area.name] = [station]
        } else {
          // else if there's already 1+ stations assigned to the planning area, but this station isn't in the array yet,
          // add it to the planning area's array
          if (
            state.stationsByPlanningArea[station.planning_area.name]?.find(
              st => st.code === station.code
            ) === undefined
          ) {
            state.stationsByPlanningArea[station.planning_area.name]?.push(station)
          }
        }
      })
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
