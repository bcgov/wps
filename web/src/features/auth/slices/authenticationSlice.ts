import { createSlice, PayloadAction } from '@reduxjs/toolkit'

import { AppThunk } from 'app/store'
import { jwtDecode } from 'jwt-decode'
import { logError } from 'utils/error'
import { isUndefined } from 'lodash'
import { TEST_AUTH, KC_AUTH_URL, KC_REALM, SM_LOGOUT_URL, KC_CLIENT } from 'utils/env'
import { ROLES } from 'features/auth/roles'
import { getKeycloakInstance, kcInitOptions } from 'features/auth/keycloak'

export interface AuthState {
  authenticating: boolean
  isAuthenticated: boolean
  tokenRefreshed: boolean
  token: string | undefined
  idToken: string | undefined
  idir: string | undefined
  email: string | undefined
  roles: string[]
  error: string | null
}

export const initialState: AuthState = {
  authenticating: false,
  isAuthenticated: false,
  tokenRefreshed: false,
  token: undefined,
  idToken: undefined,
  idir: undefined,
  email: undefined,
  roles: [],
  error: null
}

const authSlice = createSlice({
  name: 'authentication',
  initialState,
  reducers: {
    authenticateStart(state: AuthState) {
      state.authenticating = true
    },
    authenticateFinished(
      state: AuthState,
      action: PayloadAction<{
        isAuthenticated: boolean
        token: string | undefined
        idToken: string | undefined
      }>
    ) {
      state.authenticating = false
      state.isAuthenticated = action.payload.isAuthenticated
      state.token = action.payload.token
      state.idToken = action.payload.idToken
      state.roles = decodeRoles(action.payload.token)
      const userDetails = decodeUserDetails(action.payload.token)
      state.idir = userDetails?.idir
      state.email = userDetails?.email
    },
    authenticateError(state: AuthState, action: PayloadAction<string>) {
      state.authenticating = false
      state.isAuthenticated = false
      state.error = action.payload
      state.roles = []
    },
    refreshTokenFinished(
      state: AuthState,
      action: PayloadAction<{
        tokenRefreshed: boolean
        token: string | undefined
        idToken: string | undefined
      }>
    ) {
      state.token = action.payload.token
      state.idToken = action.payload.idToken
      state.tokenRefreshed = action.payload.tokenRefreshed
      state.roles = decodeRoles(action.payload.token)
      const userDetails = decodeUserDetails(action.payload.token)
      state.idir = userDetails?.idir
      state.email = userDetails?.email
    },
    signoutFinished(state: AuthState) {
      state.authenticating = false
      state.isAuthenticated = false
      state.token = undefined
      state.idToken = undefined
      state.roles = []
    },
    signoutError(state: AuthState, action: PayloadAction<string>) {
      state.authenticating = false
      state.isAuthenticated = false
      state.error = action.payload
      state.token = undefined
      state.idToken = undefined
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
  const decodedToken: any = jwtDecode(token)
  try {
    if (!isUndefined(decodedToken.client_roles)) {
      return decodedToken.client_roles
    }
    return []
  } catch (e) {
    // User has no roles
    return []
  }
}

export const decodeUserDetails = (token: string | undefined) => {
  if (isUndefined(token)) {
    return undefined
  }
  if (TEST_AUTH || window.Cypress) {
    return { idir: 'test@idir', email: 'test@example.com' }
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const decodedToken: any = jwtDecode(token)
  try {
    return { idir: decodedToken.idir_username, email: decodedToken.email }
  } catch (e) {
    // No idir username
    return undefined
  }
}

export const testAuthenticate =
  (isAuthenticated: boolean, token: string, idToken: string): AppThunk =>
  dispatch => {
    dispatch(authenticateFinished({ isAuthenticated, token, idToken }))
  }

export const authenticate = (): AppThunk => dispatch => {
  dispatch(authenticateStart())

  const keycloak = getKeycloakInstance()
  keycloak
    .init(kcInitOptions)
    .then(isAuthenticated => {
      dispatch(authenticateFinished({ isAuthenticated, token: keycloak?.token, idToken: keycloak?.idToken }))
    })
    .catch(err => {
      logError(err)
      dispatch(authenticateError('Failed to authenticate.'))
    })

  keycloak.onTokenExpired = () => {
    keycloak
      ?.updateToken(0)
      .then(tokenRefreshed => {
        dispatch(refreshTokenFinished({ tokenRefreshed, token: keycloak?.token, idToken: keycloak?.idToken }))
      })
      .catch(() => {
        // Restart the authentication flow
        dispatch(authenticate())
      })
  }
}

export const signout =
  (idToken?: string): AppThunk =>
  async dispatch => {
    try {
      const postLogoutRedirectURI = window.location.href
      const keycloakLogoutUrl = encodeURIComponent(
        `${KC_AUTH_URL}/realms/${KC_REALM}/protocol/openid-connect/logout?client_id=${KC_CLIENT}&id_token_hint=${idToken}&post_logout_redirect_uri=${postLogoutRedirectURI}`
      )
      const logoutURL = `${SM_LOGOUT_URL}${keycloakLogoutUrl}`
      window.location.href = logoutURL
    } catch (e) {
      return dispatch(signoutError(`Failed to sign out: ${e}`))
    }
  }
