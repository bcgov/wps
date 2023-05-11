import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'

interface State {
  wf1Token: string | undefined
  error: string | null
}

export const initialState: State = {
  wf1Token: undefined,
  error: null
}

const wf1AuthSlice = createSlice({
  name: 'wf1Authentication',
  initialState,
  reducers: {
    authenticated(
      state: State,
      action: PayloadAction<{
        wf1Token: string | undefined
      }>
    ) {
      state.wf1Token = action.payload.wf1Token
    },
    unAuthenticated(state: State) {
      state.wf1Token = undefined
    },
    authenticateError(
      state: State,
      action: PayloadAction<{
        error: string
      }>
    ) {
      state.wf1Token = undefined
      state.error = action.payload.error
    }
  }
})

export const { authenticated, unAuthenticated, authenticateError } = wf1AuthSlice.actions

export default wf1AuthSlice.reducer

export const wf1Authenticate =
  (wf1Token: string): AppThunk =>
  dispatch => {
    dispatch(authenticated({ wf1Token }))
  }

export const wf1Signout = (): AppThunk => async dispatch => {
  dispatch(unAuthenticated())
}

export const wf1AuthenticateError =
  (error: string): AppThunk =>
  dispatch => {
    dispatch(authenticateError({ error }))
  }
