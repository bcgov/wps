import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getStationGroupsMembers, StationGroupMember } from 'api/stationAPI'

interface State {
  loading: boolean
  error: string | null
  members: StationGroupMember[]
}

export const initialState: State = {
  loading: false,
  error: null,
  members: []
}

const selectedStationGroupsMembersSlice = createSlice({
  name: 'selectedStationGroupsMembers',
  initialState,
  reducers: {
    getStationGroupsMembersStart(state: State) {
      state.error = null
      state.loading = true
    },
    getStationGroupsMembersFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getStationGroupsMembersSuccess(state: State, action: PayloadAction<StationGroupMember[]>) {
      state.error = null
      state.members = action.payload
      state.loading = false
    }
  }
})

export const { getStationGroupsMembersStart, getStationGroupsMembersFailed, getStationGroupsMembersSuccess } =
  selectedStationGroupsMembersSlice.actions

export default selectedStationGroupsMembersSlice.reducer

export const fetchStationGroupsMembers =
  (groupIds: string[]): AppThunk =>
  async dispatch => {
    try {
      dispatch(getStationGroupsMembersStart())
      const members = await getStationGroupsMembers(groupIds)
      dispatch(getStationGroupsMembersSuccess(members))
    } catch (err) {
      dispatch(getStationGroupsMembersFailed((err as Error).toString()))
      logError(err)
    }
  }
