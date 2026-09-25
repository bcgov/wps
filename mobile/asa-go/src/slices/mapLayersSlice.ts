import { createSlice } from '@reduxjs/toolkit'

export interface MapLayersState {
  pendingLoads: number
  latestErrorVersion: number
}

export const initialState: MapLayersState = {
  pendingLoads: 0,
  latestErrorVersion: 0
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
    },
    mapLayerLoadFailed(state: MapLayersState) {
      // keep failures occurrence-based because another layer succeeding does not prove this one recovered
      state.latestErrorVersion += 1
    }
  }
})

export const { mapLayerLoadFailed, mapLayerLoadFinished, mapLayerLoadStarted } = mapLayersSlice.actions

export default mapLayersSlice.reducer
