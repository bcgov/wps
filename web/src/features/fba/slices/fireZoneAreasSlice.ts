import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FireShapeArea, FireShapeAreaListResponse, getFireShapeAreas } from 'api/fbaAPI'
import { RunType } from 'features/fba/pages/FireBehaviourAdvisoryPage'

interface State {
  loading: boolean
  error: string | null
  fireShapeAreas: FireShapeArea[]
}

const initialState: State = {
  loading: false,
  error: null,
  fireShapeAreas: []
}

const fireShapeAreasSlice = createSlice({
  name: 'fireShapeAreas',
  initialState,
  reducers: {
    getFireShapeAreasStart(state: State) {
      state.error = null
      state.loading = true
      state.fireShapeAreas = []
    },
    getFireShapeAreasFailed(state: State, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireShapeAreasSuccess(state: State, action: PayloadAction<FireShapeAreaListResponse>) {
      state.error = null
      state.fireShapeAreas = action.payload.shapes
      state.loading = false
    }
  }
})

export const { getFireShapeAreasStart, getFireShapeAreasFailed, getFireShapeAreasSuccess } = fireShapeAreasSlice.actions

export default fireShapeAreasSlice.reducer

export const fetchFireShapeAreas =
  (runType: RunType, run_datetime: string, for_date: string): AppThunk =>
  async dispatch => {
    if (run_datetime != undefined && run_datetime !== ``) {
      try {
        dispatch(getFireShapeAreasStart())
        const fireShapeAreas = await getFireShapeAreas(runType, run_datetime, for_date)
        dispatch(getFireShapeAreasSuccess(fireShapeAreas))
      } catch (err) {
        dispatch(getFireShapeAreasFailed((err as Error).toString()))
        logError(err)
      }
    } else {
      try {
        dispatch(getFireShapeAreasFailed('run_datetime cannot be undefined!'))
      } catch (err) {
        dispatch(getFireShapeAreasFailed((err as Error).toString()))
        logError(err)
      }
    }
  }
