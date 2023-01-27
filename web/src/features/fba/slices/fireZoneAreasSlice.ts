import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FireZoneArea, ZoneAreaListResponse, getFireZoneAreas } from 'api/fbaAPI'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'

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
  (runType: RunType, run_datetime: string, for_date: string): AppThunk =>
  async dispatch => {
    if (run_datetime != undefined && run_datetime !== ``) {
      try {
        dispatch(getFireZoneAreasStart())
        const fireZoneAreas = await getFireZoneAreas(runType, run_datetime, for_date)
        console.log(fireZoneAreas)
        dispatch(getFireZoneAreasSuccess(fireZoneAreas))
      } catch (err) {
        dispatch(getFireZoneAreasFailed((err as Error).toString()))
        logError(err)
      }
    } else {
      try {
        dispatch(getFireZoneAreasFailed('run_datetime cannot be undefined!'))
      } catch (err) {
        dispatch(getFireZoneAreasFailed((err as Error).toString()))
        logError(err)
      }
    }
  }
