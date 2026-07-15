import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import { TEST_AUTH } from '@wps/utils/env'
import { logError } from '@wps/utils/error'
import type { AppThunk } from 'app/store'
import { getKeycloakInstance, kcInitOptions } from 'features/auth/keycloak'
import { ROLES } from 'features/auth/roles'
import type { KeycloakTokenParsed } from 'keycloak-js'
import { isUndefined } from 'lodash'

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
        tokenParsed: KeycloakTokenParsed | undefined
      }>
    ) {
      state.authenticating = false
      state.isAuthenticated = action.payload.isAuthenticated
      state.token = action.payload.token
      state.idToken = action.payload.idToken
      state.roles = decodeRoles(action.payload.tokenParsed)
      const userDetails = decodeUserDetails(action.payload.tokenParsed)
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
        tokenParsed: KeycloakTokenParsed | undefined
      }>
    ) {
      state.token = action.payload.token
      state.idToken = action.payload.idToken
      state.tokenRefreshed = action.payload.tokenRefreshed
      state.roles = decodeRoles(action.payload.tokenParsed)
      const userDetails = decodeUserDetails(action.payload.tokenParsed)
      state.idir = userDetails?.idir
      state.email = userDetails?.email
    }
  }
})

export const { authenticateStart, authenticateFinished, authenticateError, refreshTokenFinished } = authSlice.actions

export default authSlice.reducer

export const decodeRoles = (tokenParsed: KeycloakTokenParsed | undefined) => {
  if (TEST_AUTH || window.Playwright) {
    return Object.values(ROLES.HFI)
  }
  if (isUndefined(tokenParsed) || isUndefined(tokenParsed.client_roles)) {
    return []
  }
  return tokenParsed.client_roles
}

export const decodeUserDetails = (tokenParsed: KeycloakTokenParsed | undefined) => {
  if (TEST_AUTH || window.Playwright) {
    return { idir: 'test@idir', email: 'test@example.com' }
  }
  if (isUndefined(tokenParsed)) {
    return undefined
  }
  return { idir: tokenParsed.idir_username, email: tokenParsed.email }
}

export const testAuthenticate =
  (isAuthenticated: boolean, token: string, idToken: string): AppThunk =>
  dispatch => {
    dispatch(authenticateFinished({ isAuthenticated, token, idToken, tokenParsed: undefined }))
  }

export const authenticate = (): AppThunk<Promise<void>> => async dispatch => {
  dispatch(authenticateStart())

  const keycloak = getKeycloakInstance()
  try {
    const isAuthenticated = await keycloak.init(kcInitOptions)
    dispatch(
      authenticateFinished({
        isAuthenticated,
        token: keycloak.token,
        idToken: keycloak.idToken,
        tokenParsed: keycloak.tokenParsed
      })
    )
  } catch (err) {
    logError(err)
    dispatch(authenticateError('Failed to authenticate.'))
  }

  keycloak.onTokenExpired = () => {
    void (async () => {
      try {
        const tokenRefreshed = await keycloak.updateToken(0)
        dispatch(
          refreshTokenFinished({
            tokenRefreshed,
            token: keycloak.token,
            idToken: keycloak.idToken,
            tokenParsed: keycloak.tokenParsed
          })
        )
      } catch {
        // Restart the authentication flow
        void dispatch(authenticate())
      }
    })()
  }
}
