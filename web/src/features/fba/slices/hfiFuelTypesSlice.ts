import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getAllRunDates, getHFIThresholdsFuelTypes } from 'api/fbaAPI'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'

interface State {
  loading: boolean
  error: string | null
}

const initialState: State = {
  loading: false,
  error: null
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
    getHFIFuelsStartSuccess(state: State) {
      state.error = null
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
      const runDates = await getAllRunDates(runType, forDate)
      const zonesThresholdsFuelTypes = await getHFIThresholdsFuelTypes(runType, forDate, runDatetime)
      dispatch(getHFIFuelsStartSuccess())
    } catch (err) {
      dispatch(getHFIFuelsFailed((err as Error).toString()))
      logError(err)
    }
  }
