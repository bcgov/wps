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
                if (station.planning_area && station.planning_area.fire_centre) {
                    state.fireCentres.push(station.planning_area.fire_centre)
                    const planningAreaName = station.planning_area.name
                    const fireCentreName = station.planning_area.fire_centre.name
                    if (state.planningAreasByFireCentre[fireCentreName] == undefined) {
                        state.planningAreasByFireCentre[fireCentreName] = [station.planning_area]
                    } else {
                        state.planningAreasByFireCentre[fireCentreName]?.push(station.planning_area)
                    }
                    if (state.stationsByPlanningArea[planningAreaName] == undefined) {
                        state.stationsByPlanningArea[planningAreaName] = [station]
                    } else {
                        state.stationsByPlanningArea[planningAreaName]?.push(station)
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
