import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getStationGroupsMembers, StationGroupMember } from 'api/stationAPI'

export interface SelectedStationGroupState {
  loading: boolean
  error: string | null
  members: StationGroupMember[]
}

export const initialState: SelectedStationGroupState = {
  loading: false,
  error: null,
  members: []
}

const selectedStationGroupsMembersSlice = createSlice({
  name: 'selectedStationGroupsMembers',
  initialState,
  reducers: {
    getStationGroupsMembersStart(state: SelectedStationGroupState) {
      state.error = null
      state.loading = true
    },
    getStationGroupsMembersFailed(state: SelectedStationGroupState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getStationGroupsMembersSuccess(state: SelectedStationGroupState, action: PayloadAction<StationGroupMember[]>) {
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
