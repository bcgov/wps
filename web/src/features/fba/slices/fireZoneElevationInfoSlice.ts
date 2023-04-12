import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { ElevationInfoByThreshold, FireZoneElevationInfoResponse, getFireZoneElevationInfo } from 'api/fbaAPI'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'
import { isNull } from 'lodash'

interface State {
  loading: boolean
  error: string | null
  fireZoneElevationInfo: ElevationInfoByThreshold[]
}

const initialState: State = {
  loading: false,
  error: null,
  fireZoneElevationInfo: []
}

const fireZoneElevationInfoSlice = createSlice({
  name: 'fireZoneElevationInfo',
  initialState,
  reducers: {
    getFireZoneElevationInfoStart(state: State) {
      state.error = null
      state.fireZoneElevationInfo = []
      state.loading = true
    },
    getFireZoneElevationInfoFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireZoneElevationInfoStartSuccess(state: State, action: PayloadAction<FireZoneElevationInfoResponse>) {
      state.error = null
      state.fireZoneElevationInfo = action.payload.hfi_elevation_info
      state.loading = false
    }
  }
})

export const { getFireZoneElevationInfoStart, getFireZoneElevationInfoFailed, getFireZoneElevationInfoStartSuccess } =
  fireZoneElevationInfoSlice.actions

export default fireZoneElevationInfoSlice.reducer

export const fetchfireZoneElevationInfo =
  (fire_zone_id: number, runType: RunType, forDate: string | null, runDatetime: string | null): AppThunk =>
  async dispatch => {
    if (!isNull(forDate) && !isNull(runDatetime)) {
      try {
        dispatch(getFireZoneElevationInfoStart())
        const fireZoneElevationInfo = await getFireZoneElevationInfo(fire_zone_id, runType, forDate, runDatetime)
        dispatch(getFireZoneElevationInfoStartSuccess(fireZoneElevationInfo))
      } catch (err) {
        dispatch(getFireZoneElevationInfoFailed((err as Error).toString()))
        logError(err)
      }
    }
  }
