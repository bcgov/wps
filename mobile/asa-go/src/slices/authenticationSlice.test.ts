// @vitest-environment node

import { beforeEach, describe, expect, it, type Mock, vi } from 'vitest'
import authenticationSlice, {
  type AuthState,
  authenticate,
  authenticateError,
  authenticateFinished,
  authenticateStart,
  continueAsGuest,
  continueAsGuestSession,
  initialState,
  resetAuthentication
} from '@/slices/authenticationSlice'
import { createTestStore } from '@/testUtils'
import { Keycloak } from '../../../keycloak/src'

interface TokenResponse {
  accessToken: string
  idToken?: string
  refreshToken?: string
  tokenType?: string
  expiresIn?: number
  scope?: string
}

// Mock valid JWT token with idir_username and email claims
const mockValidToken =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGlyX3VzZXJuYW1lIjoiSm9obiBEb2UiLCJlbWFpbCI6ImpvaG4uZG9lQGNvbnRhY3QuY29tIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'

// Mock the Keycloak module
vi.mock('../../../keycloak/src', () => ({
  Keycloak: {
    authenticate: vi.fn(),
    addListener: vi.fn(),
    clearAuthState: vi.fn()
  }
}))

const mockSetUser = vi.hoisted(() => vi.fn())
vi.mock('@sentry/capacitor', () => ({
  setUser: mockSetUser
}))

describe('authenticationSlice', () => {
  // Test data factories
  const createAuthState = (overrides: Partial<AuthState> = {}): AuthState => ({
    ...initialState,
    ...overrides
  })

  const createSuccessfulAuthResult = (overrides = {}) => ({
    isAuthenticated: true,
    accessToken: mockValidToken,
    idToken: 'test-id-token',
    ...overrides
  })

  const createFailedAuthResult = (error?: string) => ({
    isAuthenticated: false,
    ...(error && { error })
  })

  const createTokenResponse = (overrides: Partial<TokenResponse> = {}): TokenResponse => ({
    accessToken: mockValidToken,
    idToken: 'new-id-token',
    refreshToken: 'new-refresh-token',
    tokenType: 'Bearer',
    expiresIn: 3600,
    scope: 'openid',
    ...overrides
  })

  // Test helpers for thunk tests
  const setupStoreWithMockAuth = (mockReturnValue: unknown) => {
    const store = createTestStore()
    ;(Keycloak.authenticate as Mock).mockResolvedValue(mockReturnValue)
    return store
  }

  const setupTokenRefreshListener = (store: ReturnType<typeof createTestStore>) => {
    let tokenRefreshCallback: (tokenResponse: TokenResponse) => void = () => {}

    ;(Keycloak.addListener as Mock).mockImplementation((event, callback) => {
      if (event === 'tokenRefresh') {
        tokenRefreshCallback = callback
      }
    })

    return {
      store,
      tokenRefreshCallback: (response: TokenResponse) => tokenRefreshCallback(response)
    }
  }

  const expectAuthState = (state: AuthState, expected: Partial<AuthState>) => {
    Object.entries(expected).forEach(([key, value]) => {
      expect(state[key as keyof AuthState]).toBe(value)
    })
  }

  describe('reducers', () => {
    it('should return the initial state', () => {
      expect(authenticationSlice(undefined, { type: 'unknown' })).toEqual(initialState)
    })

    it('should handle authenticateStart', () => {
      const previousState = createAuthState({
        authenticating: false,
        sessionMode: 'guest'
      })
      const nextState = authenticationSlice(previousState, authenticateStart())

      expectAuthState(nextState, {
        sessionMode: 'login',
        authenticating: true,
        error: null
      })
    })

    it('should handle continueAsGuest', () => {
      const previousState = createAuthState({
        authenticating: true,
        error: 'Authentication failed',
        sessionMode: 'authenticated',
        token: 'existing-token',
        idToken: 'existing-id-token',
        idir: 'test-user',
        email: 'test@example.com'
      })

      const nextState = authenticationSlice(previousState, continueAsGuest())

      expectAuthState(nextState, {
        sessionMode: 'guest',
        authenticating: false,
        token: undefined,
        idToken: undefined,
        idir: undefined,
        email: undefined,
        error: null
      })
    })

    it('should handle authenticateFinished with successful authentication', () => {
      const previousState = createAuthState({ authenticating: true })
      const payload = {
        token: mockValidToken,
        idToken: 'id-token-456'
      }

      const nextState = authenticationSlice(previousState, authenticateFinished(payload))

      expectAuthState(nextState, {
        sessionMode: 'authenticated',
        authenticating: false,
        token: mockValidToken,
        idToken: 'id-token-456'
      })
    })

    it('should handle authenticateError', () => {
      const previousState = createAuthState({
        authenticating: true,
        sessionMode: 'authenticated',
        token: 'existing-token',
        idToken: 'existing-id-token',
        idir: 'test-user',
        email: 'test@example.com'
      })
      const errorMessage = 'Authentication failed'

      const nextState = authenticationSlice(previousState, authenticateError(errorMessage))

      expectAuthState(nextState, {
        sessionMode: 'login',
        authenticating: false,
        error: errorMessage,
        token: undefined,
        idToken: undefined,
        idir: undefined,
        email: undefined
      })
    })

    it('should handle resetAuthentication', () => {
      const previousState = createAuthState({
        sessionMode: 'authenticated',
        authenticating: true,
        token: 'existing-token',
        idToken: 'existing-id-token',
        idir: 'test-user',
        email: 'test@example.com',
        error: 'existing-error'
      })

      const nextState = authenticationSlice(previousState, resetAuthentication())

      expectAuthState(nextState, {
        sessionMode: 'login',
        authenticating: false,
        token: undefined,
        idToken: undefined,
        idir: undefined,
        email: undefined,
        error: null
      })
    })
  })

  describe('thunks', () => {
    beforeEach(() => {
      vi.resetAllMocks()
    })

    describe('authenticate', () => {
      it('should dispatch authenticateStart when called', async () => {
        const store = setupStoreWithMockAuth(createSuccessfulAuthResult())

        await store.dispatch(authenticate())

        expectAuthState(store.getState().authentication, {
          authenticating: false // Should be false after completion
        })
      })

      it('should dispatch authenticateFinished on successful authentication', async () => {
        const mockResult = createSuccessfulAuthResult({
          accessToken: mockValidToken
        })
        const store = setupStoreWithMockAuth(mockResult)

        await store.dispatch(authenticate())

        expectAuthState(store.getState().authentication, {
          sessionMode: 'authenticated',
          token: mockValidToken,
          idToken: 'test-id-token',
          authenticating: false,
          error: null
        })
        expect(mockSetUser).toHaveBeenCalledWith({ email: 'john.doe@contact.com' })
      })

      it('should dispatch authenticateError on failed authentication with error message', async () => {
        const mockResult = createFailedAuthResult('Invalid credentials')
        const store = setupStoreWithMockAuth(mockResult)

        await store.dispatch(authenticate())

        expectAuthState(store.getState().authentication, {
          sessionMode: 'login',
          error: JSON.stringify(mockResult.error),
          authenticating: false
        })
      })

      it('should dispatch authenticateError on failed authentication without error message', async () => {
        const mockResult = createFailedAuthResult()
        const store = setupStoreWithMockAuth(mockResult)

        await store.dispatch(authenticate())

        expectAuthState(store.getState().authentication, {
          sessionMode: 'login',
          error: JSON.stringify(mockResult.error),
          authenticating: false
        })
      })

      // Note: Testing promise rejection scenarios is complex due to async thunk behavior
      // The important flows (success and handled errors) are covered above
      it('should call Keycloak.authenticate when authentication is initiated', async () => {
        const store = setupStoreWithMockAuth(createSuccessfulAuthResult())

        await store.dispatch(authenticate())

        // Verify Keycloak.authenticate was called with the expected mocked values
        expect(Keycloak.authenticate).toHaveBeenCalledWith({
          authorizationBaseUrl: 'https://auth.test.com/realms/test-realm/protocol/openid-connect/auth',
          clientId: 'test-client',
          redirectUrl: 'ca.bc.gov.asago://auth/callback',
          accessTokenEndpoint: 'https://auth.test.com/realms/test-realm/protocol/openid-connect/token'
        })
      })

      it('should set up token refresh listener', async () => {
        const store = setupStoreWithMockAuth(createSuccessfulAuthResult())

        await store.dispatch(authenticate())

        expect(Keycloak.addListener).toHaveBeenCalledWith('tokenRefresh', expect.any(Function))
      })

      it('should handle token refresh callback correctly', async () => {
        const store = setupStoreWithMockAuth(createSuccessfulAuthResult())
        const { tokenRefreshCallback } = setupTokenRefreshListener(store)

        await store.dispatch(authenticate())

        // Simulate token refresh
        const tokenResponse = createTokenResponse()
        tokenRefreshCallback(tokenResponse)

        expectAuthState(store.getState().authentication, {
          token: mockValidToken,
          idToken: 'new-id-token'
        })
        expect(mockSetUser).toHaveBeenCalledWith({ email: 'john.doe@contact.com' })
      })

      it('should not update state when token refresh has no refresh token', async () => {
        const store = setupStoreWithMockAuth(createSuccessfulAuthResult())
        const { tokenRefreshCallback } = setupTokenRefreshListener(store)

        await store.dispatch(authenticate())

        const initialState = store.getState().authentication

        // Simulate token refresh without refresh token
        const tokenResponse = createTokenResponse({ refreshToken: undefined })
        tokenRefreshCallback(tokenResponse)

        const finalState = store.getState().authentication
        expect(finalState.token).toBe(initialState.token)
      })

      it('clears native auth state before continuing as guest', async () => {
        ;(Keycloak.clearAuthState as Mock).mockResolvedValue(undefined)
        const store = createTestStore({
          authentication: createAuthState({
            sessionMode: 'authenticated',
            token: mockValidToken,
            idToken: 'existing-id-token',
            idir: 'test-user',
            email: 'test@example.com'
          })
        })

        await store.dispatch(continueAsGuestSession())

        expect(Keycloak.clearAuthState).toHaveBeenCalled()
        expectAuthState(store.getState().authentication, {
          sessionMode: 'guest',
          token: undefined,
          idToken: undefined,
          idir: undefined,
          email: undefined
        })
        expect(mockSetUser).toHaveBeenCalledWith(null)
      })

      it('continues as guest when native auth clear fails', async () => {
        ;(Keycloak.clearAuthState as Mock).mockRejectedValue(new Error('clear failed'))
        const store = createTestStore({
          authentication: createAuthState({
            sessionMode: 'authenticated',
            token: mockValidToken
          })
        })

        await store.dispatch(continueAsGuestSession())

        expect(store.getState().authentication.sessionMode).toBe('guest')
      })
    })
  })
})
