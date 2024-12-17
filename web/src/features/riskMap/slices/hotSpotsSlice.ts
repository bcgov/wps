import { getHotSpots } from '@/api/riskMapAPI'
import { hotSpotCSVToGeoJSON } from '@/features/riskMap/spatialOperations'
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { DateTime } from 'luxon'

export interface HotSpotsState {
  loading: boolean
  error: string | null
  hotSpotPoints: any
}

const initialState: HotSpotsState = {
  loading: false,
  error: null,
  hotSpotPoints: []
}

const hotSpotsSlice = createSlice({
  name: 'hotSpotPoints',
  initialState,
  reducers: {
    getHotSpotsStart(state: HotSpotsState) {
      state.error = null
      state.loading = true
      state.hotSpotPoints = ''
    },
    getHotSpotsFailed(state: HotSpotsState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getHotSpotsSuccess(state: HotSpotsState, action: PayloadAction<any>) {
      state.error = null
      state.hotSpotPoints = action.payload
      state.loading = false
    }
  }
})

export const { getHotSpotsStart, getHotSpotsFailed, getHotSpotsSuccess } = hotSpotsSlice.actions

export default hotSpotsSlice.reducer

export const fetchHotSpots =
  (dateOfInterest: DateTime): AppThunk =>
  async dispatch => {
    try {
      dispatch(getHotSpotsStart())
      const hotSpotsData = await getHotSpots(dateOfInterest)
      const hotSpotGeoJSON = hotSpotCSVToGeoJSON(hotSpotsData)
      dispatch(getHotSpotsSuccess(hotSpotGeoJSON))
    } catch (err) {
      dispatch(getHotSpotsFailed((err as Error).toString()))
    }
  }
