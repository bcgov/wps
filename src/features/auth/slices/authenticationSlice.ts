import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import axios from 'api/axios'
import { AppThunk } from 'app/store'
import { selectToken } from 'app/rootReducer'
import kcInstance, { kcInitOption } from 'features/auth/keycloak'

interface State {
  authenticating: boolean
  isAuthenticated: boolean
  tokenRefreshed: boolean
  token: string | undefined
  error: string | null
}

export const initialState: State = {
  authenticating: false,
  isAuthenticated: false,
  tokenRefreshed: false,
  token: undefined,
  error: null
}

const authSlice = createSlice({
  name: 'authentication',
  initialState,
  reducers: {
    authenticateStart(state: State) {
      state.authenticating = true
    },
    authenticateFinished(
      state: State,
      action: PayloadAction<{
        isAuthenticated: boolean
        token: string | undefined
      }>
    ) {
      state.authenticating = false
      state.isAuthenticated = action.payload.isAuthenticated
      state.token = action.payload.token
    },
    authenticateError(state: State, action: PayloadAction<string>) {
      state.authenticating = false
      state.isAuthenticated = false
      state.error = action.payload
    },
    refreshTokenFinished(
      state: State,
      action: PayloadAction<{
        tokenRefreshed: boolean
        token: string | undefined
      }>
    ) {
      state.token = action.payload.token
      state.tokenRefreshed = action.payload.tokenRefreshed
    }
  }
})

export const {
  authenticateStart,
  authenticateFinished,
  authenticateError,
  refreshTokenFinished
} = authSlice.actions

export default authSlice.reducer

export const authenticate = (): AppThunk => dispatch => {
  dispatch(authenticateStart())
  kcInstance
    .init(kcInitOption)
    .then(isAuthenticated => {
      dispatch(authenticateFinished({ isAuthenticated, token: kcInstance.token }))
    })
    .catch(err => {
      console.error(err)
      dispatch(authenticateError('Failed to authenticate.'))
    })
  // Set a callback that will be triggered when the access token is expired
  kcInstance.onTokenExpired = () => {
    kcInstance
      .updateToken(0)
      .then(tokenRefreshed => {
        dispatch(refreshTokenFinished({ tokenRefreshed, token: kcInstance.token }))
      })
      .catch(() => {
        // Restart the flow
        dispatch(authenticate())
      })
  }
}

export const setAxiosRequestInterceptors = (): AppThunk => (_, getState) => {
  // Use axios interceptors to intercept any requests and add authorization headers.
  axios.interceptors.request.use(config => {
    const token = selectToken(getState())
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  })
}
