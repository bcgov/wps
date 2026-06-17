import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import {
  type ElevationInfoByThreshold,
  type FireZoneElevationInfoResponse,
  getFireZoneElevationInfo,
  type RunType
} from '@wps/api/fbaAPI'
import { logError } from '@wps/utils/error'
import type { AppThunk } from 'app/store'

export interface ZoneElevationInfoState {
  loading: boolean
  error: string | null
  fireZoneElevationInfo: ElevationInfoByThreshold[]
}

const initialState: ZoneElevationInfoState = {
  loading: false,
  error: null,
  fireZoneElevationInfo: []
}

const fireZoneElevationInfoSlice = createSlice({
  name: 'fireZoneElevationInfo',
  initialState,
  reducers: {
    getFireZoneElevationInfoStart(state: ZoneElevationInfoState) {
      state.error = null
      state.fireZoneElevationInfo = []
      state.loading = true
    },
    getFireZoneElevationInfoFailed(state: ZoneElevationInfoState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireZoneElevationInfoStartSuccess(
      state: ZoneElevationInfoState,
      action: PayloadAction<FireZoneElevationInfoResponse>
    ) {
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
  (fire_zone_id: number, runType: RunType, forDate: string, runDatetime: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(getFireZoneElevationInfoStart())
      const fireZoneElevationInfo = await getFireZoneElevationInfo(fire_zone_id, runType, forDate, runDatetime)
      dispatch(getFireZoneElevationInfoStartSuccess(fireZoneElevationInfo))
    } catch (err) {
      dispatch(getFireZoneElevationInfoFailed((err as Error).toString()))
      logError(err)
    }
  }
