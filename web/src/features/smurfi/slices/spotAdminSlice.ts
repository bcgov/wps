import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { RootState } from '@/app/rootReducer'
import { SpotAdminRow, SpotForecastStatus } from '@/features/smurfi/interfaces'
import { getSpotAdminRows } from '@/api/SMURFIAPI'
import { DateTime } from 'luxon'

export interface SpotAdminState {
  loading: boolean
  error: string | null
  spotAdminRows: SpotAdminRow[]
}

export const initialState: SpotAdminState = {
  loading: false,
  error: null,
  spotAdminRows: [
    {
      id: 1,
      spot_id: 123,
      fire_id: 'V0800168',
      forecaster: 'Matt',
      fire_centre: 'Coastal',
      status: SpotForecastStatus.NEW,
      last_updated: null,
      latitude: 49.6188,
      longitude: -125.0313,
      spot_start: DateTime.now().plus({ days: -1 }).toMillis(),
      spot_end: DateTime.now().plus({ days: 9 }).toMillis()
    },
    {
      id: 2,
      spot_id: 124,
      fire_id: 'G0700234',
      forecaster: 'Jessie',
      fire_centre: 'Prince George',
      status: SpotForecastStatus.ACTIVE,
      last_updated: DateTime.now().toMillis(),
      latitude: 53.9171,
      longitude: -122.7497,
      spot_start: DateTime.now().toMillis(),
      spot_end: DateTime.now().plus({ days: 10 }).toMillis()
    },
    {
      id: 3,
      spot_id: 125,
      fire_id: 'K0300789',
      forecaster: 'Brett',
      fire_centre: 'Kamloops',
      status: SpotForecastStatus.PAUSED,
      last_updated: DateTime.now().toMillis(),
      latitude: 50.9171,
      longitude: -122.7497,
      spot_start: DateTime.now().plus({ days: -5 }).toMillis(),
      spot_end: DateTime.now().plus({ days: 5 }).toMillis()
    },
    {
      id: 4,
      spot_id: 126,
      fire_id: 'C092346',
      forecaster: 'Liz',
      fire_centre: 'Cariboo',
      status: SpotForecastStatus.INACTIVE,
      last_updated: DateTime.now().toMillis(),
      latitude: 54.9171,
      longitude: -125.7497,
      spot_start: DateTime.now().plus({ days: -10 }).toMillis(),
      spot_end: DateTime.now().plus({ days: -1 }).toMillis()
    },
    {
      id: 5,
      spot_id: 127,
      fire_id: 'C092347',
      forecaster: 'Matt',
      fire_centre: 'Southeast',
      status: SpotForecastStatus.ARCHIVED,
      last_updated: DateTime.now().toMillis(),
      latitude: 50.9171,
      longitude: -125.7497,
      spot_start: DateTime.now().plus({ days: -15 }).toMillis(),
      spot_end: DateTime.now().plus({ days: -55 }).toMillis()
    }
  ]
}

const spotAdminSlice = createSlice({
  name: 'spotAdmin',
  initialState,
  reducers: {
    getSpotAdminStart(state: SpotAdminState) {
      state.error = null
      state.loading = true
      state.spotAdminRows = []
    },
    getSpotAdminFailed(state: SpotAdminState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getSpotAdminSuccess(state: SpotAdminState, action: PayloadAction<SpotAdminRow[]>) {
      state.error = null
      state.spotAdminRows = action.payload
      state.loading = false
    },
    updateSpotAdminStart(state: SpotAdminState) {
      state.error = null
      state.loading = true
    },
    updateSpotAdminSuccess(state: SpotAdminState, action: PayloadAction<SpotAdminRow>) {
      state.spotAdminRows = state.spotAdminRows.map(item => (item.id === action.payload.id ? action.payload : item))
      state.error = null
      state.loading = false
    }
  }
})

export const {
  getSpotAdminStart,
  getSpotAdminFailed,
  getSpotAdminSuccess,
  updateSpotAdminStart,
  updateSpotAdminSuccess
} = spotAdminSlice.actions

export default spotAdminSlice.reducer

export const fetchSpotAdminRows = (): AppThunk => async dispatch => {
  try {
    dispatch(getSpotAdminStart())
    const { rows } = await getSpotAdminRows()
    dispatch(getSpotAdminSuccess(rows))
  } catch (err) {
    dispatch(getSpotAdminFailed((err as Error).toString()))
  }
}

export const selectSpotAdminRows = (state: RootState) => state.spotAdmin.spotAdminRows
