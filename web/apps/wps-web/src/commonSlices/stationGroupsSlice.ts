import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getStationGroups, StationGroup } from 'api/stationAPI'

export interface StationGroupsState {
  loading: boolean
  error: string | null
  groups: StationGroup[]
}

const initialState: StationGroupsState = {
  loading: false,
  error: null,
  groups: []
}

const stationGroupsSlice = createSlice({
  name: 'stationGroups',
  initialState,
  reducers: {
    getStationGroupsStart(state: StationGroupsState) {
      state.error = null
      state.loading = true
    },
    getStationGroupsFailed(state: StationGroupsState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getStationGroupsSuccess(state: StationGroupsState, action: PayloadAction<StationGroup[]>) {
      state.error = null
      state.groups = action.payload
      state.loading = false
    }
  }
})

export const { getStationGroupsStart, getStationGroupsFailed, getStationGroupsSuccess } = stationGroupsSlice.actions

export default stationGroupsSlice.reducer

export const fetchStationGroups = (): AppThunk => async dispatch => {
  try {
    dispatch(getStationGroupsStart())
    const ownedGroups = await getStationGroups()
    dispatch(getStationGroupsSuccess(ownedGroups))
  } catch (err) {
    dispatch(getStationGroupsFailed((err as Error).toString()))
    logError(err)
  }
}
