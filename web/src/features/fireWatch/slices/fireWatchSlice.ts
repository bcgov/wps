import {
  FireWatchOutput,
  getActiveFireWatches,
  postFireWatchInput,
  postFireWatchUpdate
} from '@/features/fireWatch/fireWatchApi'
import { FireWatch } from '@/features/fireWatch/interfaces'
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppThunk } from 'app/store'

export interface FireWatchState {
  loading: boolean
  error: string | null
  fireWatches: FireWatchOutput[]
  fireWatchSubmitting: boolean
  fireWatchSubmitError: string | null
}

const initialState: FireWatchState = {
  loading: false,
  error: null,
  fireWatches: [],
  fireWatchSubmitting: false,
  fireWatchSubmitError: null
}

const fireWatchSlice = createSlice({
  name: 'fireWatch',
  initialState,
  reducers: {
    getFireWatchStart(state: FireWatchState) {
      state.error = null
      state.loading = true
      state.fireWatches = []
    },
    getFireWatchFailed(state: FireWatchState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    getFireWatchSuccess(state: FireWatchState, action: PayloadAction<{ fireWatchList: FireWatchOutput[] }>) {
      state.error = null
      state.fireWatches = action.payload.fireWatchList
      state.loading = false
    },
    submitFireWatchStart(state: FireWatchState) {
      state.fireWatchSubmitError = null
      state.fireWatchSubmitting = true
    },
    submitFireWatchFailed(state: FireWatchState, action: PayloadAction<string>) {
      state.fireWatchSubmitError = action.payload
      state.fireWatchSubmitting = false
    },
    submitFireWatchSuccess(state: FireWatchState, action: PayloadAction<{ fireWatch: FireWatchOutput }>) {
      state.fireWatchSubmitting = false
      state.fireWatchSubmitError = null
      state.fireWatches = [...state.fireWatches, action.payload.fireWatch]
    }
  }
})

export const {
  getFireWatchStart,
  getFireWatchFailed,
  getFireWatchSuccess,
  submitFireWatchStart,
  submitFireWatchFailed,
  submitFireWatchSuccess
} = fireWatchSlice.actions

export default fireWatchSlice.reducer

export const fetchActiveFireWatches = (): AppThunk => async dispatch => {
  try {
    dispatch(getFireWatchStart())
    const fireWatchListResponse = await getActiveFireWatches()
    dispatch(getFireWatchSuccess({ fireWatchList: fireWatchListResponse.watch_list }))
  } catch (err) {
    dispatch(getFireWatchFailed((err as Error).toString()))
  }
}

export const submitNewFireWatch =
  (fireWatch: FireWatch): AppThunk =>
  async dispatch => {
    try {
      dispatch(submitFireWatchStart())
      const submitFireWatchResponse = await postFireWatchInput(fireWatch)
      const fireWatchOutput = submitFireWatchResponse.fire_watch
      dispatch(submitFireWatchSuccess({ fireWatch: fireWatchOutput }))
    } catch (err) {
      dispatch(submitFireWatchFailed((err as Error).toString()))
    }
  }

export const updateFireWatch =
  (fireWatch: FireWatch): AppThunk<Promise<FireWatchOutput | undefined>> =>
  async dispatch => {
    try {
      dispatch(submitFireWatchStart())
      const submitFireWatchResponse = await postFireWatchUpdate(fireWatch)
      const fireWatchOutput = submitFireWatchResponse.fire_watch
      dispatch(submitFireWatchSuccess({ fireWatch: fireWatchOutput }))
      return fireWatchOutput
    } catch (err) {
      dispatch(submitFireWatchFailed((err as Error).toString()))
    }
  }
