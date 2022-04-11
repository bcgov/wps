import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import kcInstance, { kcInitOption } from 'features/auth/keycloak'
import jwt_decode from 'jwt-decode'
import { logError } from 'utils/error'
import { isUndefined } from 'lodash'
import { KC_CLIENT } from 'utils/env'

interface State {
  authenticating: boolean
  isAuthenticated: boolean
  tokenRefreshed: boolean
  token: string | undefined
  shouldEnableFireStarts: boolean
  error: string | null
}

export const initialState: State = {
  authenticating: false,
  isAuthenticated: false,
  tokenRefreshed: false,
  token: undefined,
  shouldEnableFireStarts: false,
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
      state.shouldEnableFireStarts = fireStartsEnabled(
        action.payload.isAuthenticated,
        decodeRoles(action.payload.token)
      )
    },
    authenticateError(state: State, action: PayloadAction<string>) {
      state.authenticating = false
      state.isAuthenticated = false
      state.error = action.payload
      state.shouldEnableFireStarts = false
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
      state.shouldEnableFireStarts = fireStartsEnabled(
        state.isAuthenticated,
        decodeRoles(action.payload.token)
      )
    }
  }
})

const {
  authenticateStart,
  authenticateFinished,
  authenticateError,
  refreshTokenFinished
} = authSlice.actions

export default authSlice.reducer

export const decodeRoles = (token: string | undefined) => {
  if (isUndefined(token)) {
    return []
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const decodedToken: any = jwt_decode(token)
  try {
    return decodedToken.resource_access[KC_CLIENT].roles
  } catch (e) {
    // User has no roles
    return []
  }
}

export const fireStartsEnabled = (isAuthenticated: boolean, roles: string[]) => {
  return isAuthenticated && roles.includes('hfi_set_fire_starts')
}

export const authenticate = (): AppThunk => dispatch => {
  dispatch(authenticateStart())

  if (!kcInstance) {
    return dispatch(
      authenticateError('Failed to authenticate (Unable to fetch keycloak-js).')
    )
  }

  kcInstance
    .init(kcInitOption)
    .then(isAuthenticated => {
      dispatch(authenticateFinished({ isAuthenticated, token: kcInstance?.token }))
    })
    .catch(err => {
      logError(err)
      dispatch(authenticateError('Failed to authenticate.'))
    })
  // Set a callback that will be triggered when the access token is expired
  kcInstance.onTokenExpired = () => {
    kcInstance
      ?.updateToken(0)
      .then(tokenRefreshed => {
        dispatch(refreshTokenFinished({ tokenRefreshed, token: kcInstance?.token }))
      })
      .catch(() => {
        // Restart the authentication flow
        dispatch(authenticate())
      })
  }
}
