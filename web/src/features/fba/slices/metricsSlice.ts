import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { getAllRunDates, getHighHFIFields } from 'api/fbaAPI'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'

interface State {
  loading: boolean
  error: string | null
}

const initialState: State = {
  loading: false,
  error: null
}

const runDatesSlice = createSlice({
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

export const { getHFIFuelsStart, getHFIFuelsFailed, getHFIFuelsStartSuccess } = runDatesSlice.actions

export default runDatesSlice.reducer

export const fetchHighHFIFuelds =
  (runType: RunType, forDate: string, runDatetime: string): AppThunk =>
  async dispatch => {
    try {
      dispatch(getHFIFuelsStart())
      const runDates = await getAllRunDates(runType, forDate)
      const mostRecentRunDate = await getHighHFIFields(runType, forDate, runDatetime)
      console.log(`runDates: ${runDates}`)
      console.log(`mostRecentRunDate = ${mostRecentRunDate}`)
      dispatch(getHFIFuelsStartSuccess())
    } catch (err) {
      dispatch(getHFIFuelsFailed((err as Error).toString()))
      logError(err)
    }
  }
