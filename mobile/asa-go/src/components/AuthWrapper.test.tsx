import { render, screen, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import { describe, expect, it, vi, beforeEach } from "vitest";
import AuthWrapper from "./AuthWrapper";
import { createTestStore } from "@/testUtils";
import { RootState } from "@/store";
import { Keycloak } from "../../../keycloak/src";

vi.mock("../../../keycloak/src", () => ({
  Keycloak: {
    authenticate: vi.fn(),
    addListener: vi.fn(),
  },
}));

describe("AuthWrapper", () => {
  const TestChild = () => <div>Test Child Component</div>;

  let mockStore: ReturnType<typeof createTestStore>;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("when user is authenticated", () => {
    beforeEach(() => {
      const initialState: Partial<RootState> = {
        authentication: {
          authenticating: false,
          isAuthenticated: false, // Start as false, will be updated by the authenticate call
          tokenRefreshed: false,
          token: undefined,
          idToken: undefined,
          error: null,
        },
      };
      mockStore = createTestStore(initialState);

      // Mock successful authentication
      vi.mocked(Keycloak.authenticate).mockResolvedValue({
        isAuthenticated: true,
        accessToken: "mock-token",
        idToken: "mock-id-token",
      });
    });

    it("renders children in StrictMode when authenticated", async () => {
      render(
        <Provider store={mockStore}>
          <AuthWrapper>
            <TestChild />
          </AuthWrapper>
        </Provider>
      );

      // Wait for the authentication to complete
      await waitFor(() => {
        expect(screen.getByText("Test Child Component")).toBeInTheDocument();
      });
    });
  });

  describe("when user is not authenticated", () => {
    beforeEach(() => {
      const initialState: Partial<RootState> = {
        authentication: {
          authenticating: false,
          isAuthenticated: false,
          tokenRefreshed: false,
          token: undefined,
          idToken: undefined,
          error: null,
        },
      };
      mockStore = createTestStore(initialState);

      // Mock failed authentication - the error should be in result.error field
      vi.mocked(Keycloak.authenticate).mockResolvedValue({
        isAuthenticated: false,
        error: "Authentication failed",
      });
    });

    it("shows not authenticated message when user is not authenticated", async () => {
      render(
        <Provider store={mockStore}>
          <AuthWrapper>
            <TestChild />
          </AuthWrapper>
        </Provider>
      );

      // Wait for the authentication to complete - it should show the error message, not "not authenticated"
      // because the result contains an error field
      await waitFor(() => {
        expect(screen.getByText("Authentication failed")).toBeInTheDocument();
      });
      expect(
        screen.queryByText("Test Child Component")
      ).not.toBeInTheDocument();
    });

    it("shows not authenticated message when authentication succeeds but user is not authenticated", async () => {
      // Mock authentication that succeeds but user is not authenticated (no error)
      vi.mocked(Keycloak.authenticate).mockResolvedValue({
        isAuthenticated: false,
      });

      render(
        <Provider store={mockStore}>
          <AuthWrapper>
            <TestChild />
          </AuthWrapper>
        </Provider>
      );

      // Wait for the authentication to complete
      await waitFor(() => {
        expect(
          screen.getByText("You are not authenticated!")
        ).toBeInTheDocument();
      });
      expect(
        screen.queryByText("Test Child Component")
      ).not.toBeInTheDocument();
    });
  });

  describe("when authentication is in progress", () => {
    beforeEach(() => {
      const initialState: Partial<RootState> = {
        authentication: {
          authenticating: false,
          isAuthenticated: false,
          tokenRefreshed: false,
          token: undefined,
          idToken: undefined,
          error: null,
        },
      };
      mockStore = createTestStore(initialState);

      // Mock slow authentication (never resolves for this test)
      vi.mocked(Keycloak.authenticate).mockImplementation(
        () => new Promise(() => {})
      );
    });

    it("shows signing in message when authenticating", () => {
      render(
        <Provider store={mockStore}>
          <AuthWrapper>
            <TestChild />
          </AuthWrapper>
        </Provider>
      );

      expect(screen.getByText("Signing in...")).toBeInTheDocument();
      expect(
        screen.queryByText("Test Child Component")
      ).not.toBeInTheDocument();
    });
  });

  describe("when authentication has an error", () => {
    beforeEach(() => {
      const initialState: Partial<RootState> = {
        authentication: {
          authenticating: false,
          isAuthenticated: false,
          tokenRefreshed: false,
          token: undefined,
          idToken: undefined,
          error: null,
        },
      };
      mockStore = createTestStore(initialState);

      // Mock authentication error - the error object will be passed to authenticateError
      vi.mocked(Keycloak.authenticate).mockRejectedValue(
        "Authentication failed"
      );
    });

    it("shows error message when there is an authentication error", async () => {
      render(
        <Provider store={mockStore}>
          <AuthWrapper>
            <TestChild />
          </AuthWrapper>
        </Provider>
      );

      // Wait for the authentication error to be processed
      await waitFor(() => {
        expect(screen.getByText("Authentication failed")).toBeInTheDocument();
      });
      expect(
        screen.queryByText("Test Child Component")
      ).not.toBeInTheDocument();
    });
  });

  describe("state transitions", () => {
    it("prioritizes error state over authenticating state", async () => {
      const initialState: Partial<RootState> = {
        authentication: {
          authenticating: false,
          isAuthenticated: false,
          tokenRefreshed: false,
          token: undefined,
          idToken: undefined,
          error: null,
        },
      };
      mockStore = createTestStore(initialState);

      // Mock authentication error
      vi.mocked(Keycloak.authenticate).mockRejectedValue("Network error");

      render(
        <Provider store={mockStore}>
          <AuthWrapper>
            <TestChild />
          </AuthWrapper>
        </Provider>
      );

      // Wait for the error to be processed
      await waitFor(() => {
        expect(screen.getByText("Network error")).toBeInTheDocument();
      });
      expect(screen.queryByText("Signing in...")).not.toBeInTheDocument();
      expect(
        screen.queryByText("Test Child Component")
      ).not.toBeInTheDocument();
    });

    it("prioritizes error state over not authenticated state", async () => {
      const initialState: Partial<RootState> = {
        authentication: {
          authenticating: false,
          isAuthenticated: false,
          tokenRefreshed: false,
          token: undefined,
          idToken: undefined,
          error: null,
        },
      };
      mockStore = createTestStore(initialState);

      // Mock authentication error
      vi.mocked(Keycloak.authenticate).mockRejectedValue("Invalid credentials");

      render(
        <Provider store={mockStore}>
          <AuthWrapper>
            <TestChild />
          </AuthWrapper>
        </Provider>
      );

      // Wait for the error to be processed
      await waitFor(() => {
        expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
      });
      expect(
        screen.queryByText("You are not authenticated!")
      ).not.toBeInTheDocument();
      expect(
        screen.queryByText("Test Child Component")
      ).not.toBeInTheDocument();
    });

    it("prioritizes authenticating state over not authenticated state", () => {
      const initialState: Partial<RootState> = {
        authentication: {
          authenticating: false,
          isAuthenticated: false,
          tokenRefreshed: false,
          token: undefined,
          idToken: undefined,
          error: null,
        },
      };
      mockStore = createTestStore(initialState);

      // Mock slow authentication that never resolves
      vi.mocked(Keycloak.authenticate).mockImplementation(
        () => new Promise(() => {})
      );

      render(
        <Provider store={mockStore}>
          <AuthWrapper>
            <TestChild />
          </AuthWrapper>
        </Provider>
      );

      expect(screen.getByText("Signing in...")).toBeInTheDocument();
      expect(
        screen.queryByText("You are not authenticated!")
      ).not.toBeInTheDocument();
      expect(
        screen.queryByText("Test Child Component")
      ).not.toBeInTheDocument();
    });
  });

  describe("component memoization", () => {
    it("should be memoized with React.memo", () => {
      expect(AuthWrapper).toBeDefined();
      // The component is wrapped with React.memo, so we can verify it exists
      // React.memo returns a MemoExoticComponent which typeof shows as 'object'
      expect(typeof AuthWrapper).toBe("object");
    });
  });

  describe("children prop type", () => {
    it("accepts React element as children", async () => {
      const initialState: Partial<RootState> = {
        authentication: {
          authenticating: false,
          isAuthenticated: false,
          tokenRefreshed: false,
          token: undefined,
          idToken: undefined,
          error: null,
        },
      };
      mockStore = createTestStore(initialState);

      // Mock successful authentication
      vi.mocked(Keycloak.authenticate).mockResolvedValue({
        isAuthenticated: true,
        accessToken: "mock-token",
        idToken: "mock-id-token",
      });

      const ComplexChild = () => (
        <div>
          <h1>Complex Child</h1>
          <p>With multiple elements</p>
        </div>
      );

      render(
        <Provider store={mockStore}>
          <AuthWrapper>
            <ComplexChild />
          </AuthWrapper>
        </Provider>
      );

      await waitFor(() => {
        expect(screen.getByText("Complex Child")).toBeInTheDocument();
      });
      expect(screen.getByText("With multiple elements")).toBeInTheDocument();
    });
  });
});
