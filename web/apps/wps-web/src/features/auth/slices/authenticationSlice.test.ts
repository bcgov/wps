import { combineReducers } from '@reduxjs/toolkit'
import { getKeycloakInstance } from 'features/auth/keycloak'
import { ROLES } from 'features/auth/roles'
import authReducer, {
  authenticate,
  authenticateError,
  authenticateFinished,
  authenticateStart,
  decodeRoles,
  decodeUserDetails,
  initialState,
  refreshTokenFinished
} from 'features/auth/slices/authenticationSlice'
import type Keycloak from 'keycloak-js'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { AppDispatch } from '@/app/store'
import { createTestStore } from '@/test/testUtils'

vi.mock('features/auth/keycloak', () => ({
  getKeycloakInstance: vi.fn(),
  kcInitOptions: {}
}))

const authenticationReducer = combineReducers({ authentication: authReducer })

describe('authenticationSlice', () => {
  const testToken = 'testToken'
  const idir_username = 'test@idir'
  const email = 'test@example.com'
  const tokenParsedAllRoles = {
    idir_username,
    email,
    client_roles: Object.values(ROLES.HFI)
  }
  const tokenParsedNoRoles = {
    idir_username,
    email,
    client_roles: []
  }
  it('should return all roles of a user from a token', () => {
    const roles = decodeRoles(tokenParsedAllRoles)
    expect(roles).toEqual(Object.values(ROLES.HFI))
  })
  it('should return no roles if user token has none defined', () => {
    const roles = decodeRoles(tokenParsedNoRoles)
    expect(roles).toEqual([])
  })
  it('should return idir username from token', () => {
    const userDetails = decodeUserDetails(tokenParsedNoRoles)
    expect(userDetails).toEqual({ idir: idir_username, email })
  })
  describe('reducer', () => {
    it('should be initialized with correct state', () => {
      expect(
        authReducer(undefined, {
          type: ''
        })
      ).toEqual(initialState)
    })
    it('should set authenticate start when authenticateStart is called', () => {
      expect(authReducer(initialState, authenticateStart())).toEqual({
        ...initialState,
        authenticating: true
      })
    })
    it('should set token with roles correctly when authentication finishes', () => {
      expect(
        authReducer(
          initialState,
          authenticateFinished({
            isAuthenticated: true,
            token: testToken,
            idToken: testToken,
            tokenParsed: tokenParsedAllRoles
          })
        )
      ).toEqual({
        ...initialState,
        authenticating: false,
        isAuthenticated: true,
        idir: 'test@idir',
        email,
        token: testToken,
        idToken: testToken,
        roles: Object.values(ROLES.HFI)
      })
    })
    it('should set token without roles correctly when authentication finishes', () => {
      expect(
        authReducer(
          initialState,
          authenticateFinished({
            isAuthenticated: true,
            token: testToken,
            idToken: testToken,
            tokenParsed: tokenParsedNoRoles
          })
        )
      ).toEqual({
        ...initialState,
        authenticating: false,
        isAuthenticated: true,
        idir: 'test@idir',
        email,
        token: testToken,
        idToken: testToken,
        roles: []
      })
    })
    it('should set error state when authentication fails', () => {
      const error = 'an error occurred'
      expect(authReducer(initialState, authenticateError(error))).toEqual({
        ...initialState,
        authenticating: false,
        isAuthenticated: false,
        error,
        roles: []
      })
    })
    it('should set state correctly when token refreshes with roles', () => {
      expect(
        authReducer(
          initialState,
          refreshTokenFinished({
            tokenRefreshed: true,
            token: testToken,
            idToken: testToken,
            tokenParsed: tokenParsedAllRoles
          })
        )
      ).toEqual({
        ...initialState,
        authenticating: false,
        tokenRefreshed: true,
        token: testToken,
        idToken: testToken,
        idir: 'test@idir',
        email,
        roles: Object.values(ROLES.HFI)
      })
    })
    it('should set state correctly when token refreshes without roles', () => {
      expect(
        authReducer(
          initialState,
          refreshTokenFinished({
            tokenRefreshed: true,
            token: testToken,
            idToken: testToken,
            tokenParsed: tokenParsedNoRoles
          })
        )
      ).toEqual({
        ...initialState,
        authenticating: false,
        tokenRefreshed: true,
        token: testToken,
        idToken: testToken,
        idir: 'test@idir',
        email,
        roles: []
      })
    })
  })

  describe('authenticate thunk', () => {
    const tokenParsed = {
      idir_username: 'test@idir',
      email: 'test@example.com',
      client_roles: Object.values(ROLES.HFI)
    }

    const createMockKeycloak = (overrides: Partial<Keycloak> = {}): Keycloak =>
      ({
        token: 'access-token',
        idToken: 'id-token',
        tokenParsed,
        init: vi.fn(),
        updateToken: vi.fn(),
        onTokenExpired: undefined,
        ...overrides
      }) as unknown as Keycloak

    beforeEach(() => {
      vi.mocked(getKeycloakInstance).mockReset()
    })

    it('dispatches authenticateStart immediately', () => {
      const keycloak = createMockKeycloak({ init: vi.fn().mockReturnValue(new Promise(() => {})) })
      vi.mocked(getKeycloakInstance).mockReturnValue(keycloak)
      const store = createTestStore({ authentication: initialState }, authenticationReducer)
      const dispatch = store.dispatch as AppDispatch

      dispatch(authenticate())

      expect(store.getState().authentication.authenticating).toBe(true)
    })

    it('dispatches authenticateFinished with the parsed token on successful init', async () => {
      const keycloak = createMockKeycloak({ init: vi.fn().mockResolvedValue(true) })
      vi.mocked(getKeycloakInstance).mockReturnValue(keycloak)
      const store = createTestStore({ authentication: initialState }, authenticationReducer)
      const dispatch = store.dispatch as AppDispatch

      await dispatch(authenticate())

      expect(store.getState().authentication).toEqual({
        ...initialState,
        authenticating: false,
        isAuthenticated: true,
        token: 'access-token',
        idToken: 'id-token',
        idir: 'test@idir',
        email: 'test@example.com',
        roles: Object.values(ROLES.HFI)
      })
    })

    it('dispatches authenticateError when init rejects', async () => {
      const keycloak = createMockKeycloak({ init: vi.fn().mockRejectedValue(new Error('boom')) })
      vi.mocked(getKeycloakInstance).mockReturnValue(keycloak)
      const store = createTestStore({ authentication: initialState }, authenticationReducer)
      const dispatch = store.dispatch as AppDispatch

      await dispatch(authenticate())

      expect(store.getState().authentication).toEqual({
        ...initialState,
        authenticating: false,
        isAuthenticated: false,
        error: 'Failed to authenticate.',
        roles: []
      })
    })

    it('dispatches refreshTokenFinished when the token refreshes successfully', async () => {
      const keycloak = createMockKeycloak({
        init: vi.fn().mockResolvedValue(true),
        updateToken: vi.fn().mockResolvedValue(true)
      })
      vi.mocked(getKeycloakInstance).mockReturnValue(keycloak)
      const store = createTestStore({ authentication: initialState }, authenticationReducer)
      const dispatch = store.dispatch as AppDispatch
      await dispatch(authenticate())

      expect(keycloak.onTokenExpired).toBeInstanceOf(Function)
      keycloak.onTokenExpired?.()
      // onTokenExpired fires the refresh fire-and-forget, so wait for it to settle
      await vi.waitFor(() => expect(store.getState().authentication.tokenRefreshed).toBe(true))

      expect(store.getState().authentication).toEqual({
        ...initialState,
        authenticating: false,
        isAuthenticated: true,
        tokenRefreshed: true,
        token: 'access-token',
        idToken: 'id-token',
        idir: 'test@idir',
        email: 'test@example.com',
        roles: Object.values(ROLES.HFI)
      })
    })

    it('restarts the authentication flow when the token refresh fails', async () => {
      const keycloak = createMockKeycloak({
        init: vi.fn().mockResolvedValue(true),
        updateToken: vi.fn().mockRejectedValue(new Error('refresh failed'))
      })
      vi.mocked(getKeycloakInstance).mockReturnValue(keycloak)
      const store = createTestStore({ authentication: initialState }, authenticationReducer)
      const dispatch = store.dispatch as AppDispatch
      await dispatch(authenticate())

      keycloak.onTokenExpired?.()
      // the restart is dispatched fire-and-forget from the catch handler, so wait for it to settle
      await vi.waitFor(() => expect(keycloak.init).toHaveBeenCalledTimes(2))

      expect(getKeycloakInstance).toHaveBeenCalledTimes(2)
      expect(store.getState().authentication).toEqual({
        ...initialState,
        authenticating: false,
        isAuthenticated: true,
        token: 'access-token',
        idToken: 'id-token',
        idir: 'test@idir',
        email: 'test@example.com',
        roles: Object.values(ROLES.HFI)
      })
    })
  })
})
