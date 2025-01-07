import { getHotSpots } from '@/api/riskMapAPI'
import { DateRange } from '@/components/dateRangePicker/types'
import { hotSpotCSVToGeoJSON } from '@/features/riskMap/spatialOperations'
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'

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
  (dateRangeOfInterest: DateRange): AppThunk =>
  async dispatch => {
    try {
      dispatch(getHotSpotsStart())

      const hotSpotsData = await getHotSpots(dateRangeOfInterest.startDate!, getDifferenceInDays(dateRangeOfInterest))
      const hotSpotGeoJSON = hotSpotCSVToGeoJSON(hotSpotsData)
      dispatch(getHotSpotsSuccess(hotSpotGeoJSON))
    } catch (err) {
      dispatch(getHotSpotsFailed((err as Error).toString()))
    }
  }

function getDifferenceInDays(dateRange: DateRange): number {
  const { startDate, endDate } = dateRange

  if (startDate && endDate) {
    // Calculate the difference in milliseconds
    const diffInMs = endDate.getTime() - startDate.getTime()

    // Convert milliseconds to days
    return Math.floor(diffInMs / (1000 * 60 * 60 * 24))
  }

  return 1
}
