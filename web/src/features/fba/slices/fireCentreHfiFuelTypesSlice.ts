import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FireCentreHfiFuelsData, getHFIThresholdsFuelTypesForCentre } from 'api/fbaAPI'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'

export interface CentreHFIFuelTypeState {
  error: string | null
  fireCentreHfiFuelTypes: FireCentreHfiFuelsData
}

const initialState: CentreHFIFuelTypeState = {
  error: null,
  fireCentreHfiFuelTypes: {}
}

const fireCentreHfiFuelTypesSlice = createSlice({
  name: 'fireCentreHfiFuelTypes',
  initialState,
  reducers: {
    getFireCentreHfiFuelTypesStart(state: CentreHFIFuelTypeState) {
      state.error = null
      state.fireCentreHfiFuelTypes = {}
    },
    getFireCentreHfiFuelTypesFailed(state: CentreHFIFuelTypeState, action: PayloadAction<string>) {
      state.error = action.payload
    },
    getFireCentreHfiFuelTypesSuccess(state: CentreHFIFuelTypeState, action: PayloadAction<FireCentreHfiFuelsData>) {
      state.error = null
      state.fireCentreHfiFuelTypes = action.payload
    }
  }
})

export const { getFireCentreHfiFuelTypesStart, getFireCentreHfiFuelTypesFailed, getFireCentreHfiFuelTypesSuccess } =
  fireCentreHfiFuelTypesSlice.actions

export default fireCentreHfiFuelTypesSlice.reducer

export const fetchFireCentreHfiFuelTypes =
  (fireCentre: string, runType: RunType, forDate: string, runDatetime: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(getFireCentreHfiFuelTypesStart())
      const data = await getHFIThresholdsFuelTypesForCentre(runType, forDate, runDatetime, fireCentre)
      dispatch(getFireCentreHfiFuelTypesSuccess(data))
    } catch (err) {
      dispatch(getFireCentreHfiFuelTypesFailed((err as Error).toString()))
      logError(err)
    }
  }
