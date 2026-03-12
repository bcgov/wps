import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'
import { getFireCentres } from '@/features/fireWatch/fireWatchApi'
import { FireWatchFireCentre } from '@/features/fireWatch/interfaces'


export interface FireWatchFireCentresState {
  loading: boolean
  error: string | null
  fireCentres: FireWatchFireCentre[]
}

const initialState: FireWatchFireCentresState = {
  loading: false,
  error: null,
  fireCentres: [],
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
    getFireWatchFireCentresSuccess(
      state: FireWatchFireCentresState,
      action: PayloadAction<{ fireCentres: FireWatchFireCentre[] }>
    ) {
      state.error = null
      state.fireCentres = action.payload.fireCentres
      state.loading = false
    }
  }
})

export const { getFireWatchFireCentresStart, getFireWatchFireCentresFailed, getFireWatchFireCentresSuccess} = fireWatchFireCentresSlice.actions

export default fireWatchFireCentresSlice.reducer

export const fetchFireWatchFireCentres = (): AppThunk =>
  async dispatch => {
    try {
      dispatch(getFireWatchFireCentresStart())
      const fireCentresResponse = await getFireCentres()
      dispatch(getFireWatchFireCentresSuccess({ fireCentres: fireCentresResponse.fire_centres }))
    } catch (err) {
      dispatch(getFireWatchFireCentresFailed((err as Error).toString()))
    }
  }




