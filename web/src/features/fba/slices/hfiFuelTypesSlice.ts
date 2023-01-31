import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FireZoneThresholdFuelTypeResponse, getAllRunDates, getHFIThresholds, getHFIThresholdsFuelTypes, HfiThreshold } from 'api/fbaAPI'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'

interface State {
  loading: boolean
  error: string | null
  hfiFuelTypes: Record<number, FireZoneThresholdFuelTypeResponse[]> | null
  thresholds: Record<number, > | null
  fuelTypes: Record<number, > | null
}

const initialState: State = {
  loading: false,
  error: null,
  hfiFuelTypes: null
  thresholds: null
  fuelTypes: null
}

const hfiFuelTypesSlice = createSlice({
  name: 'runDates',
  initialState,
  reducers: {
    getHFIFuelsStart(state: State) {
      state.error = null
      state.loading = true
    },
    getHFIFuelsFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getHFIFuelsStartSuccess(state: State, action: PayloadAction<
      {
      hfiFuelTypes: Record<number, FireZoneThresholdFuelTypeResponse[]>,
      thresholds: List[HfiThreshold],
      fuelTypes: Record<number, >
    }
    > {
      state.error = null
      state.hfiFuelTypes = action.payload.hfiFuelTypes
      state.thresholds = action.payload.thresholds
      state.fuelTypes = action.payload.fuelTypes
      state.loading = false
    }
  }
})

export const { getHFIFuelsStart, getHFIFuelsFailed, getHFIFuelsStartSuccess } = hfiFuelTypesSlice.actions

export default hfiFuelTypesSlice.reducer

export const fetchHighHFIFuels =
  (runType: RunType, forDate: string, runDatetime: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(getHFIFuelsStart())
      const hfiFuelTypes = await getHFIThresholdsFuelTypes(runType, forDate, runDatetime)
      const thresholds = await getHFIThresholds()
      dispatch(getHFIFuelsStartSuccess({hfiFuelTypes: hfiFuelTypes, thresholds: thresholds}))
    } catch (err) {
      dispatch(getHFIFuelsFailed((err as Error).toString()))
      logError(err)
    }
  }
