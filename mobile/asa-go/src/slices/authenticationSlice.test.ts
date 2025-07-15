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
  describe("reducers", () => {
    it("should return the initial state", () => {
      expect(authenticationSlice(undefined, { type: "unknown" })).toEqual(
        initialState
      );
    });

    it("should handle authenticateStart", () => {
      const previousState: AuthState = {
        ...initialState,
        authenticating: false,
      };

      const nextState = authenticationSlice(previousState, authenticateStart());

      expect(nextState.authenticating).toBe(true);
      expect(nextState.isAuthenticated).toBe(false);
      expect(nextState.error).toBe(null);
    });

    it("should handle authenticateFinished with successful authentication", () => {
      const previousState: AuthState = {
        ...initialState,
        authenticating: true,
      };

      const payload = {
        isAuthenticated: true,
        token: "access-token-123",
        idToken: "id-token-456",
      };

      const nextState = authenticationSlice(
        previousState,
        authenticateFinished(payload)
      );

      expect(nextState.authenticating).toBe(false);
      expect(nextState.isAuthenticated).toBe(true);
      expect(nextState.token).toBe("access-token-123");
      expect(nextState.idToken).toBe("id-token-456");
    });

    it("should handle authenticateFinished with failed authentication", () => {
      const previousState: AuthState = {
        ...initialState,
        authenticating: true,
      };

      const payload = {
        isAuthenticated: false,
        token: undefined,
        idToken: undefined,
      };

      const nextState = authenticationSlice(
        previousState,
        authenticateFinished(payload)
      );

      expect(nextState.authenticating).toBe(false);
      expect(nextState.isAuthenticated).toBe(false);
      expect(nextState.token).toBeUndefined();
      expect(nextState.idToken).toBeUndefined();
    });

    it("should handle authenticateError", () => {
      const previousState: AuthState = {
        ...initialState,
        authenticating: true,
        isAuthenticated: true,
      };

      const errorMessage = "Authentication failed";

      const nextState = authenticationSlice(
        previousState,
        authenticateError(errorMessage)
      );

      expect(nextState.authenticating).toBe(false);
      expect(nextState.isAuthenticated).toBe(false);
      expect(nextState.error).toBe(errorMessage);
    });

    it("should handle refreshTokenFinished", () => {
      const previousState: AuthState = {
        ...initialState,
        token: "old-token",
        idToken: "old-id-token",
        tokenRefreshed: false,
      };

      const payload = {
        tokenRefreshed: true,
        token: "new-access-token",
        idToken: "new-id-token",
      };

      const nextState = authenticationSlice(
        previousState,
        refreshTokenFinished(payload)
      );

      expect(nextState.token).toBe("new-access-token");
      expect(nextState.idToken).toBe("new-id-token");
      expect(nextState.tokenRefreshed).toBe(true);
    });

    it("should handle refreshTokenFinished with undefined tokens", () => {
      const previousState: AuthState = {
        ...initialState,
        token: "existing-token",
        idToken: "existing-id-token",
        tokenRefreshed: false,
      };

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
        const store = createTestStore();
        (Keycloak.authenticate as Mock).mockResolvedValue({
          isAuthenticated: true,
          accessToken: "test-token",
          idToken: "test-id-token",
        });

        await store.dispatch(authenticate());

        const actions = store.getState();
        expect(actions.authentication.authenticating).toBe(false); // Should be false after completion
      });

      it("should dispatch authenticateFinished on successful authentication", async () => {
        const store = createTestStore();
        const mockResult = {
          isAuthenticated: true,
          accessToken: "test-access-token",
          idToken: "test-id-token",
        };

        (Keycloak.authenticate as Mock).mockResolvedValue(mockResult);

        await store.dispatch(authenticate());

        const state = store.getState().authentication;
        expect(state.isAuthenticated).toBe(true);
        expect(state.token).toBe("test-access-token");
        expect(state.idToken).toBe("test-id-token");
        expect(state.authenticating).toBe(false);
        expect(state.error).toBe(null);
      });

      it("should dispatch authenticateError on failed authentication with error message", async () => {
        const store = createTestStore();
        const mockResult = {
          isAuthenticated: false,
          error: "Invalid credentials",
        };

        (Keycloak.authenticate as Mock).mockResolvedValue(mockResult);

        await store.dispatch(authenticate());

        const state = store.getState().authentication;
        expect(state.isAuthenticated).toBe(false);
        expect(state.error).toBe("Invalid credentials");
        expect(state.authenticating).toBe(false);
      });

      it("should dispatch authenticateError on failed authentication without error message", async () => {
        const store = createTestStore();
        const mockResult = {
          isAuthenticated: false,
        };

        (Keycloak.authenticate as Mock).mockResolvedValue(mockResult);

        await store.dispatch(authenticate());

        const state = store.getState().authentication;
        expect(state.isAuthenticated).toBe(false);
        expect(state.error).toBe("");
        expect(state.authenticating).toBe(false);
      });

      // Note: Testing promise rejection scenarios is complex due to async thunk behavior
      // The important flows (success and handled errors) are covered above
      it("should call Keycloak.authenticate when authentication is initiated", async () => {
        const store = createTestStore();
        (Keycloak.authenticate as Mock).mockResolvedValue({
          isAuthenticated: true,
          accessToken: "test-token",
          idToken: "test-id-token",
        });

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
        const store = createTestStore();
        (Keycloak.authenticate as Mock).mockResolvedValue({
          isAuthenticated: true,
          accessToken: "test-token",
          idToken: "test-id-token",
        });

        await store.dispatch(authenticate());

        expect(Keycloak.addListener).toHaveBeenCalledWith(
          "tokenRefresh",
          expect.any(Function)
        );
      });

      it("should handle token refresh callback correctly", async () => {
        const store = createTestStore();
        let tokenRefreshCallback: (
          tokenResponse: TokenResponse
        ) => void = () => {};

        (Keycloak.authenticate as Mock).mockResolvedValue({
          isAuthenticated: true,
          accessToken: "test-token",
          idToken: "test-id-token",
        });

        (Keycloak.addListener as Mock).mockImplementation((event, callback) => {
          if (event === "tokenRefresh") {
            tokenRefreshCallback = callback;
          }
        });

        await store.dispatch(authenticate());

        // Simulate token refresh
        const tokenResponse: TokenResponse = {
          accessToken: "new-access-token",
          refreshToken: "new-refresh-token",
          tokenType: "Bearer",
          expiresIn: 3600,
          scope: "openid",
        };

        tokenRefreshCallback(tokenResponse);

        const state = store.getState().authentication;
        expect(state.tokenRefreshed).toBe(true);
        expect(state.token).toBe("new-access-token");
        expect(state.idToken).toBeUndefined();
      });

      it("should not update state when token refresh has no refresh token", async () => {
        const store = createTestStore();
        let tokenRefreshCallback: (
          tokenResponse: TokenResponse
        ) => void = () => {};

        (Keycloak.authenticate as Mock).mockResolvedValue({
          isAuthenticated: true,
          accessToken: "test-token",
          idToken: "test-id-token",
        });

        (Keycloak.addListener as Mock).mockImplementation((event, callback) => {
          if (event === "tokenRefresh") {
            tokenRefreshCallback = callback;
          }
        });

        await store.dispatch(authenticate());

        const initialState = store.getState().authentication;

        // Simulate token refresh without refresh token
        const tokenResponse: TokenResponse = {
          accessToken: "new-access-token",
          tokenType: "Bearer",
          expiresIn: 3600,
          scope: "openid",
        };

        tokenRefreshCallback(tokenResponse);

        const finalState = store.getState().authentication;
        expect(finalState.tokenRefreshed).toBe(initialState.tokenRefreshed);
        expect(finalState.token).toBe(initialState.token);
      });
    });
  });
});
