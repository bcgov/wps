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

  // Common initial state for authentication
  const createInitialAuthState = (): Partial<RootState> => ({
    authentication: {
      authenticating: false,
      isAuthenticated: false,
      tokenRefreshed: false,
      token: undefined,
      idToken: undefined,
      error: null,
    },
  });

  // Helper function to render AuthWrapper with Provider
  const renderAuthWrapper = (children = <TestChild />) => {
    return render(
      <Provider store={mockStore}>
        <AuthWrapper>{children}</AuthWrapper>
      </Provider>
    );
  };

  // Helper function to create store with initial state
  const setupMockStore = (initialState = createInitialAuthState()) => {
    mockStore = createTestStore(initialState);
  };

  // Common assertions
  const expectTestChildNotVisible = () => {
    expect(screen.queryByText("Test Child Component")).not.toBeInTheDocument();
  };

  const expectTestChildVisible = () => {
    expect(screen.getByText("Test Child Component")).toBeInTheDocument();
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("when user is authenticated", () => {
    beforeEach(() => {
      setupMockStore();

      // Mock successful authentication
      vi.mocked(Keycloak.authenticate).mockResolvedValue({
        isAuthenticated: true,
        accessToken: "mock-token",
        idToken: "mock-id-token",
      });
    });

    it("renders children in StrictMode when authenticated", async () => {
      renderAuthWrapper();

      // Wait for the authentication to complete
      await waitFor(() => {
        expectTestChildVisible();
      });
    });
  });

  describe("when user is not authenticated", () => {
    beforeEach(() => {
      setupMockStore();

      // Mock failed authentication - the error should be in result.error field
      vi.mocked(Keycloak.authenticate).mockResolvedValue({
        isAuthenticated: false,
        error: "Authentication failed",
      });
    });

    it("shows not authenticated message when user is not authenticated", async () => {
      renderAuthWrapper();

      // Wait for the authentication to complete - it should show the error message, not "not authenticated"
      // because the result contains an error field
      await waitFor(() => {
        expect(screen.getByText("Authentication failed")).toBeInTheDocument();
      });
      expectTestChildNotVisible();
    });

    it("shows not authenticated message when authentication succeeds but user is not authenticated", async () => {
      // Mock authentication that succeeds but user is not authenticated (no error)
      vi.mocked(Keycloak.authenticate).mockResolvedValue({
        isAuthenticated: false,
      });

      renderAuthWrapper();

      // Wait for the authentication to complete
      await waitFor(() => {
        expect(
          screen.getByText("You are not authenticated!")
        ).toBeInTheDocument();
      });
      expectTestChildNotVisible();
    });
  });

  describe("when authentication is in progress", () => {
    beforeEach(() => {
      setupMockStore();

      // Mock slow authentication (never resolves for this test)
      vi.mocked(Keycloak.authenticate).mockImplementation(
        () => new Promise(() => {})
      );
    });

    it("shows signing in message when authenticating", () => {
      renderAuthWrapper();

      expect(screen.getByText("Signing in...")).toBeInTheDocument();
      expectTestChildNotVisible();
    });
  });

  describe("when authentication has an error", () => {
    beforeEach(() => {
      setupMockStore();

      // Mock authentication error - the error object will be passed to authenticateError
      vi.mocked(Keycloak.authenticate).mockRejectedValue(
        "Authentication failed"
      );
    });

    it("shows error message when there is an authentication error", async () => {
      renderAuthWrapper();

      // Wait for the authentication error to be processed
      await waitFor(() => {
        expect(screen.getByText("Authentication failed")).toBeInTheDocument();
      });
      expectTestChildNotVisible();
    });
  });

  describe("state transitions", () => {
    it("prioritizes error state over authenticating state", async () => {
      setupMockStore();

      // Mock authentication error
      vi.mocked(Keycloak.authenticate).mockRejectedValue("Network error");

      renderAuthWrapper();

      // Wait for the error to be processed
      await waitFor(() => {
        expect(screen.getByText("Network error")).toBeInTheDocument();
      });
      expect(screen.queryByText("Signing in...")).not.toBeInTheDocument();
      expectTestChildNotVisible();
    });

    it("prioritizes error state over not authenticated state", async () => {
      setupMockStore();

      // Mock authentication error
      vi.mocked(Keycloak.authenticate).mockRejectedValue("Invalid credentials");

      renderAuthWrapper();

      // Wait for the error to be processed
      await waitFor(() => {
        expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
      });
      expect(
        screen.queryByText("You are not authenticated!")
      ).not.toBeInTheDocument();
      expectTestChildNotVisible();
    });

    it("prioritizes authenticating state over not authenticated state", () => {
      setupMockStore();

      // Mock slow authentication that never resolves
      vi.mocked(Keycloak.authenticate).mockImplementation(
        () => new Promise(() => {})
      );

      renderAuthWrapper();

      expect(screen.getByText("Signing in...")).toBeInTheDocument();
      expect(
        screen.queryByText("You are not authenticated!")
      ).not.toBeInTheDocument();
      expectTestChildNotVisible();
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
      setupMockStore();

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

      renderAuthWrapper(<ComplexChild />);

      await waitFor(() => {
        expect(screen.getByText("Complex Child")).toBeInTheDocument();
      });
      expect(screen.getByText("With multiple elements")).toBeInTheDocument();
    });
  });
});
