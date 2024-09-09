import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { StationGroupMember } from 'api/stationAPI'
import { RootState } from 'app/rootReducer'

export interface SelectedStationState {
  selectedStations: StationGroupMember[]
}

export const initialState: SelectedStationState = {
  selectedStations: []
}

const selectedStationsSlice = createSlice({
  name: 'selectedStationsSlice',
  initialState,
  reducers: {
    selectedStationsChanged(state: SelectedStationState, action: PayloadAction<StationGroupMember[]>) {
      state.selectedStations = action.payload
    }
  }
})

export const { selectedStationsChanged } = selectedStationsSlice.actions

export default selectedStationsSlice.reducer

export const selectSelectedStations = (state: RootState) => state.selectedStations.selectedStations
