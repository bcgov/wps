import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import * as Sentry from '@sentry/capacitor'
import { jwtDecode } from 'jwt-decode'
import { isUndefined } from 'lodash'
import type { AppThunk } from '@/store'
import { Keycloak } from '../../../keycloak/src'
import type { KeycloakTokenResponse } from '../../../keycloak/src/definitions'

export type AuthSessionMode = 'login' | 'guest' | 'authenticated'

export interface AuthState {
  sessionMode: AuthSessionMode
  authenticating: boolean
  token: string | undefined
  idToken: string | undefined
  idir: string | undefined
  email: string | undefined
  error: string | null
}

export const initialState: AuthState = {
  sessionMode: 'login',
  authenticating: false,
  token: undefined,
  idToken: undefined,
  idir: undefined,
  email: undefined,
  error: null
}

const authSlice = createSlice({
  name: 'authentication',
  initialState,
  reducers: {
    continueAsGuest() {
      return {
        ...initialState,
        sessionMode: 'guest' as const
      }
    },
    authenticateStart(state: AuthState) {
      state.authenticating = true
      state.sessionMode = 'login'
      state.error = null
    },
    authenticateFinished(
      state: AuthState,
      action: PayloadAction<{
        token: string | undefined
        idToken: string | undefined
      }>
    ) {
      const userDetails = decodeUserDetails(action.payload.token)
      state.idir = userDetails?.idir
      state.email = userDetails?.email
      state.authenticating = false
      state.sessionMode = 'authenticated'
      state.token = action.payload.token
      state.idToken = action.payload.idToken
    },
    authenticateError(_state: AuthState, action: PayloadAction<string>) {
      return {
        ...initialState,
        error: action.payload
      }
    },
    resetAuthentication() {
      return { ...initialState }
    }
  }
})

export const { continueAsGuest, authenticateStart, authenticateFinished, authenticateError, resetAuthentication } =
  authSlice.actions

export default authSlice.reducer

export const authenticate = (): AppThunk => dispatch => {
  dispatch(authenticateStart())

  const realm = import.meta.env.VITE_KEYCLOAK_REALM
  const authUrl = `${import.meta.env.VITE_KEYCLOAK_AUTH_URL}/realms/${realm}/protocol/openid-connect/auth`
  const tokenUrl = `${import.meta.env.VITE_KEYCLOAK_AUTH_URL}/realms/${realm}/protocol/openid-connect/token`

  const customRedirectUri = 'ca.bc.gov.asago://auth/callback'
  Keycloak.authenticate({
    authorizationBaseUrl: authUrl,
    clientId: import.meta.env.VITE_KEYCLOAK_CLIENT,
    redirectUrl: customRedirectUri,
    accessTokenEndpoint: tokenUrl
  })
    .then(result => {
      if (result.isAuthenticated) {
        dispatch(
          authenticateFinished({
            token: result.accessToken,
            idToken: result.idToken
          })
        )
        setSentryUserFromToken(result.accessToken)
      } else {
        dispatch(authenticateError(JSON.stringify(result.error)))
      }
    })
    .catch(error => {
      dispatch(authenticateError(JSON.stringify(error)))
    })

  // Handle token refresh callback function
  const handleTokenRefresh = (tokenResponse: KeycloakTokenResponse) => {
    if (tokenResponse.refreshToken) {
      dispatch(
        authenticateFinished({
          token: tokenResponse.accessToken,
          idToken: tokenResponse.idToken
        })
      )
      setSentryUserFromToken(tokenResponse.accessToken)
    }
  }

  // Set up event listener for token refresh events (works for both web and iOS)
  Keycloak.addListener('tokenRefresh', handleTokenRefresh)
}

export const decodeUserDetails = (token: string | undefined) => {
  if (isUndefined(token)) {
    return undefined
  }
  try {
    const decodedToken: any = jwtDecode(token)
    return { idir: decodedToken.idir_username, email: decodedToken.email }
  } catch (e) {
    // Handle invalid token or missing claims
    console.error(e)
    return undefined
  }
}

export const setSentryUserFromToken = (token: string | undefined) => {
  const userDetails = decodeUserDetails(token)
  Sentry.setUser(userDetails ? { email: userDetails.email } : null)
}
