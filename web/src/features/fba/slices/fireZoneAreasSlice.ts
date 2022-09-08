import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FireZoneArea, ZoneAreaListResponse, getFireZoneAreas } from 'api/fbaAPI'

interface State {
  loading: boolean
  error: string | null
  fireZoneAreas: FireZoneArea[]
}

const initialState: State = {
  loading: false,
  error: null,
  fireZoneAreas: []
}

const fireZoneAreasSlice = createSlice({
  name: 'fireZoneAreas',
  initialState,
  reducers: {
    getFireZoneAreasStart(state: State) {
      state.error = null
      state.loading = true
      state.fireZoneAreas = []
    },
    getFireZoneAreasFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireZoneAreasSuccess(state: State, action: PayloadAction<ZoneAreaListResponse>) {
      state.error = null
      state.fireZoneAreas = action.payload.zones
      state.loading = false
    }
  }
})

export const { getFireZoneAreasStart, getFireZoneAreasFailed, getFireZoneAreasSuccess } = fireZoneAreasSlice.actions

export default fireZoneAreasSlice.reducer

export const fetchFireZoneAreas =
  (for_date: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(getFireZoneAreasStart())
      // TODO: We need a mechanism to request the most recent run date for a given for_date
      const fireZoneAreas = await getFireZoneAreas('forecast', for_date, for_date)
      dispatch(getFireZoneAreasSuccess(fireZoneAreas))
    } catch (err) {
      dispatch(getFireZoneAreasFailed((err as Error).toString()))
      logError(err)
    }
  }
