import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import kcInstance, { kcInitOption } from 'features/auth/keycloak'
import * as jwtDecode from 'jwt-decode'
import { logError } from 'utils/error'
import { isUndefined } from 'lodash'
import { KC_CLIENT, TEST_AUTH, KC_AUTH_URL, KC_REALM } from 'utils/env'
import { ROLES } from 'features/auth/roles'

interface State {
  authenticating: boolean
  isAuthenticated: boolean
  tokenRefreshed: boolean
  token: string | undefined
  idir: string | undefined
  roles: string[]
  error: string | null
}

export const initialState: State = {
  authenticating: false,
  isAuthenticated: false,
  tokenRefreshed: false,
  token: undefined,
  idir: undefined,
  roles: [],
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
      state.roles = decodeRoles(action.payload.token)
      state.idir = decodeIdir(action.payload.token)
    },
    authenticateError(state: State, action: PayloadAction<string>) {
      state.authenticating = false
      state.isAuthenticated = false
      state.error = action.payload
      state.roles = []
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
      state.roles = decodeRoles(action.payload.token)
      state.idir = decodeIdir(action.payload.token)
    },
    signoutFinished(state: State) {
      state.authenticating = false
      state.isAuthenticated = false
      state.token = undefined
      state.roles = []
    },
    signoutError(state: State, action: PayloadAction<string>) {
      state.authenticating = false
      state.isAuthenticated = false
      state.error = action.payload
      state.token = undefined
      state.roles = []
    }
  }
})

export const {
  authenticateStart,
  authenticateFinished,
  authenticateError,
  refreshTokenFinished,
  signoutFinished,
  signoutError
} = authSlice.actions

export default authSlice.reducer

export const decodeRoles = (token: string | undefined) => {
  if (isUndefined(token)) {
    return []
  }
  if (TEST_AUTH || window.Cypress) {
    return Object.values(ROLES.HFI)
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const decodedToken: any = jwtDecode.default(token)
  try {
    return decodedToken.resource_access[KC_CLIENT].roles
  } catch (e) {
    // User has no roles
    return []
  }
}

export const decodeIdir = (token: string | undefined) => {
  if (isUndefined(token)) {
    return undefined
  }
  if (TEST_AUTH || window.Cypress) {
    return 'test@idir'
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const decodedToken: any = jwtDecode.default(token)
  try {
    return decodedToken.preferred_username
  } catch (e) {
    // No idir username
    return undefined
  }
}

export const testAuthenticate =
  (isAuthenticated: boolean, token: string): AppThunk =>
  dispatch => {
    dispatch(authenticateFinished({ isAuthenticated, token }))
  }

export const authenticate = (): AppThunk => dispatch => {
  dispatch(authenticateStart())

  if (!kcInstance) {
    return dispatch(authenticateError('Failed to authenticate (Unable to fetch keycloak-js).'))
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

export const signout = (): AppThunk => async dispatch => {
  if (!kcInstance) {
    return dispatch(signoutError('Failed to authenticate (Unable to fetch keycloak-js).'))
  }

  try {
    const postLogoutRedirectURI = window.location.href
    const returl = encodeURIComponent(
      `${KC_AUTH_URL}/realms/${KC_REALM}/protocol/openid-connect/logout?post_logout_redirect_uri=${postLogoutRedirectURI}`
    )
    const logoutURL = `https://logontest7.gov.bc.ca/clp-cgi/logoff.cgi?retnow=1&returl=${returl}`
    window.location.href = logoutURL
  } catch (e) {
    return dispatch(signoutError(`Failed to signout: ${e}`))
  }
}
