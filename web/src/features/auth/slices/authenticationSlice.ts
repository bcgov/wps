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

export const cypressAuthFinished = (): AppThunk => dispatch => {
  const token =
    'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJQZUlFYlpQUm5xaTk2ZDl6RFJZT3B5RFBqVHdkei1tcF9kRHJPYmJ4Uko0In0.eyJleHAiOjE2NDk0NTYyMDksImlhdCI6MTY0OTQ1NDQwOSwiYXV0aF90aW1lIjoxNjQ5NDQ3Njg4LCJqdGkiOiI5OGMxZDM1ZC1lYWU4LTQzNTItOWE0Yy04ZTk3ZWY4NTJmMWUiLCJpc3MiOiJodHRwczovL2Rldi5vaWRjLmdvdi5iYy5jYS9hdXRoL3JlYWxtcy84d2w2eDRjcCIsInN1YiI6ImQ4MWI3MTkwLTUzMmItNDNhYi05Y2ZmLWZlOThjMGJlNjNhZSIsInR5cCI6IkJlYXJlciIsImF6cCI6Indwcy13ZWIiLCJub25jZSI6IjIxMWM3NjgzLTQ2M2EtNDMwNC04NThlLWNmYjA0MzA0MjhlMSIsInNlc3Npb25fc3RhdGUiOiIwMGJmNTQ0Mi0yNjliLTQ5MTYtOTAyOS1iMTllMmUyNDM0MmUiLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbIioiXSwicmVzb3VyY2VfYWNjZXNzIjp7Indwcy13ZWIiOnsicm9sZXMiOlsiaGZpX3NlbGVjdF9zdGF0aW9uIiwidGVzdC1yb2xlIiwiaGZpX3NldF9maXJlX3N0YXJ0cyJdfX0sInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsIm5hbWUiOiJDb25vciBCcmFkeSIsInByZWZlcnJlZF91c2VybmFtZSI6ImNicmFkeUBpZGlyIiwiZ2l2ZW5fbmFtZSI6IkNvbm9yIiwiZmFtaWx5X25hbWUiOiJCcmFkeSIsImVtYWlsIjoiY29ub3IuYnJhZHlAZ292LmJjLmNhIn0.gmJyQqjqtmxwj-eD57cN2_om_5J8GsDlCyeFcEueTMtc_JhKxJDgH90LVUQ0HizdZObpid61cjUJnogb6gyPrzJgesb2FEZaMd88ACU9akbHvYhe4TrBjDPGev5XE9SdMpag8vbVsNa4JIUn6KQxUDhJw8a_olTsqunTT5KKdrPSQyCExk6nDFGE2lZqgDUDIszbpLkzv7xV9T9MOoWeVDJSQvfw3aH4ZXUZ26rxt4RQGDJTInHO6M91zwWPc6Gi0KPxMNv7DG7eyJ8FWg1e8WeptZ6gdcKFgGEIY8lih2TdmeP40gzti1KpBXbMVwLavlXbS46wHgXQTbm-2CW6mQ'
  dispatch(authenticateFinished({ isAuthenticated: true, token }))
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
