import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getStationGroups, StationGroup } from 'api/stationAPI'

interface State {
  loading: boolean
  error: string | null
  groups: StationGroup[]
}

const initialState: State = {
  loading: false,
  error: null,
  groups: []
}

const stationGroupsSlice = createSlice({
  name: 'fireCenters',
  initialState,
  reducers: {
    getStationGroupsStart(state: State) {
      state.error = null
      state.loading = true
    },
    getStationGroupsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getStationGroupsSuccess(state: State, action: PayloadAction<StationGroup[]>) {
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
