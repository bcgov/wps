import { createSlice } from '@reduxjs/toolkit'

export interface MapLayersState {
  pendingLoads: number
}

export const initialState: MapLayersState = {
  pendingLoads: 0
}

const mapLayersSlice = createSlice({
  name: 'mapLayers',
  initialState,
  reducers: {
    mapLayerLoadStarted(state: MapLayersState) {
      state.pendingLoads += 1
    },
    mapLayerLoadFinished(state: MapLayersState) {
      state.pendingLoads = Math.max(0, state.pendingLoads - 1)
    }
  }
})

export const { mapLayerLoadFinished, mapLayerLoadStarted } = mapLayersSlice.actions

export default mapLayersSlice.reducer
