import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FireZoneThresholdFuelTypeArea, getHFIThresholdsFuelTypesForZone } from 'api/fbaAPI'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'

export interface HFIFuelTypeState {
  loading: boolean
  error: string | null
  hfiThresholdsFuelTypes: Record<number, FireZoneThresholdFuelTypeArea[]>
}

const initialState: HFIFuelTypeState = {
  loading: false,
  error: null,
  hfiThresholdsFuelTypes: {}
}

const hfiFuelTypesSlice = createSlice({
  name: 'hfiFuelTypes',
  initialState,
  reducers: {
    getHFIFuelsStart(state: HFIFuelTypeState) {
      state.error = null
      state.loading = true
      state.hfiThresholdsFuelTypes = {}
    },
    getHFIFuelsFailed(state: HFIFuelTypeState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getHFIFuelsStartSuccess(
      state: HFIFuelTypeState,
      action: PayloadAction<Record<number, FireZoneThresholdFuelTypeArea[]>>
    ) {
      state.error = null
      state.hfiThresholdsFuelTypes = action.payload
      state.loading = false
    }
  }
})

export const { getHFIFuelsStart, getHFIFuelsFailed, getHFIFuelsStartSuccess } = hfiFuelTypesSlice.actions

export default hfiFuelTypesSlice.reducer

export const fetchHighHFIFuels =
  (runType: RunType, forDate: string, runDatetime: string, zoneID: number): AppThunk =>
  async dispatch => {
    try {
      dispatch(getHFIFuelsStart())
      const data = await getHFIThresholdsFuelTypesForZone(runType, forDate, runDatetime, zoneID)
      dispatch(getHFIFuelsStartSuccess(data))
    } catch (err) {
      dispatch(getHFIFuelsFailed((err as Error).toString()))
      logError(err)
    }
  }
