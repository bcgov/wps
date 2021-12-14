import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FBAResponse, FireBehaviourAdvisory, getFBAs } from 'api/fbaAPI'
import { getFireBehaviourStationsFailed } from 'features/fbaCalculator/slices/fbaCalculatorSlice'

interface State {
  loading: boolean
  error: string | null
  date: string | null
  fireBehaviourAdvisories: FireBehaviourAdvisory[]
}

const initialState: State = {
  loading: false,
  error: null,
  date: null,
  fireBehaviourAdvisories: []
}

const fireBehaviourAdvisoriesSlice = createSlice({
  name: 'fireBehaviourAdvisories',
  initialState,
  reducers: {
    getFireBehaviourAdvisoriesStart(state: State) {
      state.error = null
      state.loading = true
      state.fireBehaviourAdvisories = []
      state.date = null
    },
    getFireBehaviourAdvisoriesFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireBehaviourAdvisoriesSuccess(state: State, action: PayloadAction<FBAResponse>) {
      state.error = null
      state.date = action.payload.date
      state.fireBehaviourAdvisories = action.payload.fireBehaviourAdvisories
      state.loading = false
    }
  }
})

export const {
  getFireBehaviourAdvisoriesStart,
  getFireBehaviourAdvisoriesFailed,
  getFireBehaviourAdvisoriesSuccess
} = fireBehaviourAdvisoriesSlice.actions

export default fireBehaviourAdvisoriesSlice.reducer

export const fetchFBAsForStations =
  (date: string): AppThunk =>
  async dispatch => {
    const formattedDate = date.slice(0, 10)
    try {
      dispatch(getFireBehaviourAdvisoriesStart())
      const fireBehaviourAdvisories = await getFBAs(formattedDate)
      dispatch(getFireBehaviourAdvisoriesSuccess(fireBehaviourAdvisories))
    } catch (err) {
      dispatch(getFireBehaviourStationsFailed((err as Error).toString()))
      logError(err)
    }
  }
