import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface AuthenticationState {
  isAuthenticated: boolean
  error: string | null
}

export const authenticationInitialState: AuthenticationState = {
  isAuthenticated: false,
  error: null
}

const auth = createSlice({
  name: 'authentication',
  initialState: authenticationInitialState,
  reducers: {
    getAuthenticationStart(state: AuthenticationState) {
      state.isAuthenticated = false
    },
    getAuthenticationFailed(
      state: AuthenticationState,
      action: PayloadAction<string>
    ) {
      state.isAuthenticated = false
      state.error = action.payload
    },
    getAuthenticationSuccess(
      state: AuthenticationState,
      action: PayloadAction<boolean>
    ) {
      state.isAuthenticated = action.payload
    },
    resetAuthentication(state: AuthenticationState) {
      state.isAuthenticated = false
    }
  }
})

export const {
  getAuthenticationStart,
  getAuthenticationFailed,
  getAuthenticationSuccess,
  resetAuthentication
} = auth.actions

export default auth.reducer
