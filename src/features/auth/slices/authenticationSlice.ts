import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import kcInstance, { kcInitOption } from 'features/auth/keycloak'

interface State {
  authenticating: boolean
  isAuthenticated: boolean
  error: string | null
}

export const initialState: State = {
  authenticating: false,
  isAuthenticated: false,
  error: null
}

const auth = createSlice({
  name: 'authentication',
  initialState,
  reducers: {
    authenticationStart(state: State) {
      state.authenticating = true
    },
    authenticationFinished(state: State, action: PayloadAction<boolean>) {
      state.authenticating = false
      state.isAuthenticated = action.payload
    },
    authenticationError(state: State, action: PayloadAction<string>) {
      state.authenticating = false
      state.isAuthenticated = false
      state.error = action.payload
    },
    resetAuthentication(state: State) {
      state.isAuthenticated = false
    }
  }
})

export const {
  authenticationStart,
  authenticationFinished,
  authenticationError,
  resetAuthentication
} = auth.actions

export default auth.reducer

export const authenticate = (): AppThunk => dispatch => {
  dispatch(authenticationStart())
  kcInstance
    .init(kcInitOption)
    .then(isAuthenticated => {
      dispatch(authenticationFinished(isAuthenticated))
    })
    .catch(err => {
      console.error(err)
      dispatch(authenticationError('Failed to authenticate.'))
    })
}
