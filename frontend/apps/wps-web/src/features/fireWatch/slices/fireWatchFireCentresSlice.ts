import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { FireCentresResponse, getFireCentres } from '@wps/api/psuAPI'
import { AppThunk } from 'app/store'
import { FireWatchFireCentre } from '@/features/fireWatch/interfaces'

export interface FireWatchFireCentresState {
  loading: boolean
  error: string | null
  fireCentres: FireWatchFireCentre[]
}

const initialState: FireWatchFireCentresState = {
  loading: false,
  error: null,
  fireCentres: []
}

const fireWatchFireCentresSlice = createSlice({
  name: 'fireWatchFireCentres',
  initialState,
  reducers: {
    getFireWatchFireCentresStart(state: FireWatchFireCentresState) {
      state.error = null
      state.loading = true
      state.fireCentres = []
    },
    getFireWatchFireCentresFailed(state: FireWatchFireCentresState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireWatchFireCentresSuccess(state: FireWatchFireCentresState, action: PayloadAction<FireCentresResponse>) {
      state.error = null
      state.fireCentres = action.payload.fire_centres
      state.loading = false
    }
  }
})

export const { getFireWatchFireCentresStart, getFireWatchFireCentresFailed, getFireWatchFireCentresSuccess } =
  fireWatchFireCentresSlice.actions

export default fireWatchFireCentresSlice.reducer

export const fetchFireWatchFireCentres = (): AppThunk => async dispatch => {
  try {
    dispatch(getFireWatchFireCentresStart())
    const fireCentresResponse = await getFireCentres()
    dispatch(getFireWatchFireCentresSuccess(fireCentresResponse))
  } catch (err) {
    dispatch(getFireWatchFireCentresFailed((err as Error).toString()))
  }
}
