import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import Feature from 'ol/Feature'
import { Geometry } from 'ol/geom'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'

export interface FireGrowthState {
  day: number
  dayGrowthLayers: any[]
}

const initialState: FireGrowthState = {
  day: 0,
  dayGrowthLayers: []
}

const fireGrowthSlice = createSlice({
  name: 'fireGrowth',
  initialState,
  reducers: {
    incrementDay(state: FireGrowthState) {
      state.day = state.day < 4 ? state.day + 1 : 1
    },
    resetDay(state: FireGrowthState) {
      state.day = 0
    },
    setDay(state: FireGrowthState, action: PayloadAction<number>) {
      state.day = action.payload
    },
    addGrowthLayer(
      state: FireGrowthState,
      action: PayloadAction<VectorLayer<VectorSource<Feature<Geometry>>, Feature<Geometry>>>
    ) {
      state.dayGrowthLayers = [...state.dayGrowthLayers, action.payload]
    }
  }
})

export const { incrementDay, resetDay, setDay, addGrowthLayer } = fireGrowthSlice.actions

export default fireGrowthSlice.reducer
