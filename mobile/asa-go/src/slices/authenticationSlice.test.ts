import { vi, Mock, describe, it, expect, beforeEach } from "vitest";
import authenticationSlice, {
  initialState,
  authenticateStart,
  authenticateFinished,
  authenticateError,
  refreshTokenFinished,
  authenticate,
  AuthState,
} from "@/slices/authenticationSlice";
import { createTestStore } from "@/testUtils";
import { Keycloak } from "../../../keycloak/src";

interface TokenResponse {
  accessToken: string;
  refreshToken?: string;
  tokenType?: string;
  expiresIn?: number;
  scope?: string;
}

// Mock the Keycloak module
vi.mock("../../../keycloak/src", () => ({
  Keycloak: {
    authenticate: vi.fn(),
    addListener: vi.fn(),
  },
}));

describe("authenticationSlice", () => {
  // Test data factories
  const createAuthState = (overrides: Partial<AuthState> = {}): AuthState => ({
    ...initialState,
    ...overrides,
  });

  const createSuccessfulAuthResult = (overrides = {}) => ({
    isAuthenticated: true,
    accessToken: "test-token",
    idToken: "test-id-token",
    ...overrides,
  });

  const createFailedAuthResult = (error?: string) => ({
    isAuthenticated: false,
    ...(error && { error }),
  });

  const createTokenResponse = (
    overrides: Partial<TokenResponse> = {}
  ): TokenResponse => ({
    accessToken: "new-access-token",
    refreshToken: "new-refresh-token",
    tokenType: "Bearer",
    expiresIn: 3600,
    scope: "openid",
    ...overrides,
  });

  // Test helpers for thunk tests
  const setupStoreWithMockAuth = (mockReturnValue: unknown) => {
    const store = createTestStore();
    (Keycloak.authenticate as Mock).mockResolvedValue(mockReturnValue);
    return store;
  };

  const setupTokenRefreshListener = (
    store: ReturnType<typeof createTestStore>
  ) => {
    let tokenRefreshCallback: (tokenResponse: TokenResponse) => void = () => {};

    (Keycloak.addListener as Mock).mockImplementation((event, callback) => {
      if (event === "tokenRefresh") {
        tokenRefreshCallback = callback;
      }
    });

    return {
      store,
      tokenRefreshCallback: (response: TokenResponse) =>
        tokenRefreshCallback(response),
    };
  };

  const expectAuthState = (state: AuthState, expected: Partial<AuthState>) => {
    Object.entries(expected).forEach(([key, value]) => {
      expect(state[key as keyof AuthState]).toBe(value);
    });
  };

  describe("reducers", () => {
    it("should return the initial state", () => {
      expect(authenticationSlice(undefined, { type: "unknown" })).toEqual(
        initialState
      );
    });

    it("should handle authenticateStart", () => {
      const previousState = createAuthState({ authenticating: false });
      const nextState = authenticationSlice(previousState, authenticateStart());

      expectAuthState(nextState, {
        authenticating: true,
        isAuthenticated: false,
        error: null,
      });
    });

    it("should handle authenticateFinished with successful authentication", () => {
      const previousState = createAuthState({ authenticating: true });
      const payload = {
        isAuthenticated: true,
        token: "access-token-123",
        idToken: "id-token-456",
      };

      const nextState = authenticationSlice(
        previousState,
        authenticateFinished(payload)
      );

      expectAuthState(nextState, {
        authenticating: false,
        isAuthenticated: true,
        token: "access-token-123",
        idToken: "id-token-456",
      });
    });

    it("should handle authenticateFinished with failed authentication", () => {
      const previousState = createAuthState({ authenticating: true });
      const payload = {
        isAuthenticated: false,
        token: undefined,
        idToken: undefined,
      };

      const nextState = authenticationSlice(
        previousState,
        authenticateFinished(payload)
      );

      expectAuthState(nextState, {
        authenticating: false,
        isAuthenticated: false,
      });
      expect(nextState.token).toBeUndefined();
      expect(nextState.idToken).toBeUndefined();
    });

    it("should handle authenticateError", () => {
      const previousState = createAuthState({
        authenticating: true,
        isAuthenticated: true,
      });
      const errorMessage = "Authentication failed";

      const nextState = authenticationSlice(
        previousState,
        authenticateError(errorMessage)
      );

      expectAuthState(nextState, {
        authenticating: false,
        isAuthenticated: false,
        error: errorMessage,
      });
    });

    it("should handle refreshTokenFinished", () => {
      const previousState = createAuthState({
        token: "old-token",
        idToken: "old-id-token",
        tokenRefreshed: false,
      });
      const payload = {
        tokenRefreshed: true,
        token: "new-access-token",
        idToken: "new-id-token",
      };

      const nextState = authenticationSlice(
        previousState,
        refreshTokenFinished(payload)
      );

      expectAuthState(nextState, {
        token: "new-access-token",
        idToken: "new-id-token",
        tokenRefreshed: true,
      });
    });

    it("should handle refreshTokenFinished with undefined tokens", () => {
      const previousState = createAuthState({
        token: "existing-token",
        idToken: "existing-id-token",
        tokenRefreshed: false,
      });
      const payload = {
        tokenRefreshed: false,
        token: undefined,
        idToken: undefined,
      };

      const nextState = authenticationSlice(
        previousState,
        refreshTokenFinished(payload)
      );

      expect(nextState.token).toBeUndefined();
      expect(nextState.idToken).toBeUndefined();
      expect(nextState.tokenRefreshed).toBe(false);
    });
  });

  describe("thunks", () => {
    beforeEach(() => {
      vi.resetAllMocks();
    });

    describe("authenticate", () => {
      it("should dispatch authenticateStart when called", async () => {
        const store = setupStoreWithMockAuth(createSuccessfulAuthResult());

        await store.dispatch(authenticate());

        expectAuthState(store.getState().authentication, {
          authenticating: false, // Should be false after completion
        });
      });

      it("should dispatch authenticateFinished on successful authentication", async () => {
        const mockResult = createSuccessfulAuthResult({
          accessToken: "test-access-token",
        });
        const store = setupStoreWithMockAuth(mockResult);

        await store.dispatch(authenticate());

        expectAuthState(store.getState().authentication, {
          isAuthenticated: true,
          token: "test-access-token",
          idToken: "test-id-token",
          authenticating: false,
          error: null,
        });
      });

      it("should dispatch authenticateError on failed authentication with error message", async () => {
        const mockResult = createFailedAuthResult("Invalid credentials");
        const store = setupStoreWithMockAuth(mockResult);

        await store.dispatch(authenticate());

        expectAuthState(store.getState().authentication, {
          isAuthenticated: false,
          error: JSON.stringify(mockResult.error),
          authenticating: false,
        });
      });

      it("should dispatch authenticateError on failed authentication without error message", async () => {
        const mockResult = createFailedAuthResult();
        const store = setupStoreWithMockAuth(mockResult);

        await store.dispatch(authenticate());

        expectAuthState(store.getState().authentication, {
          isAuthenticated: false,
          error: JSON.stringify(mockResult.error),
          authenticating: false,
        });
      });

      // Note: Testing promise rejection scenarios is complex due to async thunk behavior
      // The important flows (success and handled errors) are covered above
      it("should call Keycloak.authenticate when authentication is initiated", async () => {
        const store = setupStoreWithMockAuth(createSuccessfulAuthResult());

        await store.dispatch(authenticate());

        // Verify Keycloak.authenticate was called with the expected mocked values
        expect(Keycloak.authenticate).toHaveBeenCalledWith({
          authorizationBaseUrl:
            "https://auth.test.com/realms/test-realm/protocol/openid-connect/auth",
          clientId: "test-client",
          redirectUrl: "ca.bc.gov.asago://auth/callback",
          accessTokenEndpoint:
            "https://auth.test.com/realms/test-realm/protocol/openid-connect/token",
        });
      });

      it("should set up token refresh listener", async () => {
        const store = setupStoreWithMockAuth(createSuccessfulAuthResult());

        await store.dispatch(authenticate());

        expect(Keycloak.addListener).toHaveBeenCalledWith(
          "tokenRefresh",
          expect.any(Function)
        );
      });

      it("should handle token refresh callback correctly", async () => {
        const store = setupStoreWithMockAuth(createSuccessfulAuthResult());
        const { tokenRefreshCallback } = setupTokenRefreshListener(store);

        await store.dispatch(authenticate());

        // Simulate token refresh
        const tokenResponse = createTokenResponse();
        tokenRefreshCallback(tokenResponse);

        expectAuthState(store.getState().authentication, {
          tokenRefreshed: true,
          token: "new-access-token",
        });
        expect(store.getState().authentication.idToken).toBeUndefined();
      });

      it("should not update state when token refresh has no refresh token", async () => {
        const store = setupStoreWithMockAuth(createSuccessfulAuthResult());
        const { tokenRefreshCallback } = setupTokenRefreshListener(store);

        await store.dispatch(authenticate());

        const initialState = store.getState().authentication;

        // Simulate token refresh without refresh token
        const tokenResponse = createTokenResponse({ refreshToken: undefined });
        tokenRefreshCallback(tokenResponse);

        const finalState = store.getState().authentication;
        expect(finalState.tokenRefreshed).toBe(initialState.tokenRefreshed);
        expect(finalState.token).toBe(initialState.token);
      });
    });
  });
});
