import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { logError } from 'utils/error'
import { FireShapeArea, FireShapeAreaListResponse, getFireShapeAreas, RunType } from 'api/fbaAPI'
import { isNull, isUndefined } from 'lodash'

export interface FireZoneAreasState {
  loading: boolean
  error: string | null
  fireShapeAreas: FireShapeArea[]
}

export const initialState: FireZoneAreasState = {
  loading: false,
  error: null,
  fireShapeAreas: []
}

const fireShapeAreasSlice = createSlice({
  name: 'fireShapeAreas',
  initialState,
  reducers: {
    getFireShapeAreasStart(state: FireZoneAreasState) {
      state.error = null
      state.loading = true
      state.fireShapeAreas = []
    },
    getFireShapeAreasFailed(state: FireZoneAreasState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireShapeAreasSuccess(state: FireZoneAreasState, action: PayloadAction<FireShapeAreaListResponse>) {
      state.error = null
      state.fireShapeAreas = action.payload.shapes
      state.loading = false
    }
  }
})

export const { getFireShapeAreasStart, getFireShapeAreasFailed, getFireShapeAreasSuccess } = fireShapeAreasSlice.actions

export default fireShapeAreasSlice.reducer

export const fetchFireShapeAreas =
  (runType: RunType, run_datetime: string | null, for_date: string): AppThunk =>
  async dispatch => {
    if (!isUndefined(run_datetime) && !isNull(run_datetime)) {
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
        dispatch(getFireShapeAreasSuccess({ shapes: [] }))
      } catch (err) {
        dispatch(getFireShapeAreasFailed((err as Error).toString()))
        logError(err)
      }
    }
  }
