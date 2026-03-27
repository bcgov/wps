import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { FireCentre, FireCentresResponse, getFireCentres } from '@wps/api/psuAPI'
import { logError } from '@wps/utils/error'

export interface FireCentresState {
  loading: boolean
  error: string | null
  fireCentres: FireCentre[]
}

const initialState: FireCentresState = {
  loading: false,
  error: null,
  fireCentres: []
}

const fireCentresSlice = createSlice({
  name: 'fireCentres',
  initialState,
  reducers: {
    getFireCentresStart(state: FireCentresState) {
      state.error = null
      state.loading = true
      state.fireCentres = []
    },
    getFireCentresFailed(state: FireCentresState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireCentresSuccess(state: FireCentresState, action: PayloadAction<FireCentresResponse>) {
      state.error = null
      state.fireCentres = action.payload.fire_centres
      state.loading = false
    }
  }
})

export const { getFireCentresStart, getFireCentresFailed, getFireCentresSuccess } = fireCentresSlice.actions

export default fireCentresSlice.reducer

export const fetchFireCentres = (): AppThunk => async dispatch => {
  try {
    dispatch(getFireCentresStart())
    const fireCentres = await getFireCentres()
    dispatch(getFireCentresSuccess(fireCentres))
  } catch (err) {
    dispatch(getFireCentresFailed((err as Error).toString()))
    logError(err)
  }
}
