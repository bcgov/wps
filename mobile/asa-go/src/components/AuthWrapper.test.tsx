import * as selectors from "@/store";
import { createTestStore } from "@/testUtils";
import * as capacitor from "@capacitor/core";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AuthWrapper from "./AuthWrapper";

// Mock LoginButton and AsaIcon
vi.mock("@/components/LoginButton", () => ({
  default: ({ label }: { label: string }) => <button>{label}</button>,
}));

vi.mock("@/assets/asa-go-transparent.png", () => ({
  default: "mocked-image.png",
}));

// Create a typed mock store
const mockStore = createTestStore();
const theme = createTheme();

const renderWithProviders = (children = <div>Protected</div>) =>
  render(
    <Provider store={mockStore}>
      <ThemeProvider theme={theme}>
        <AuthWrapper>{children}</AuthWrapper>
      </ThemeProvider>
    </Provider>
  );

describe("AuthWrapper", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders children when platform is android", () => {
    vi.spyOn(capacitor.Capacitor, "getPlatform").mockReturnValue("android");
    vi.spyOn(selectors, "selectAuthentication").mockReturnValue({
      isAuthenticated: false,
      authenticating: false,
      error: null,
      tokenRefreshed: false,
      idToken: undefined,
      token: "test-token",
    });

    renderWithProviders();

    expect(screen.getByText("Protected")).toBeInTheDocument();
  });

  it("renders children when authenticated", () => {
    vi.spyOn(capacitor.Capacitor, "getPlatform").mockReturnValue("web");
    vi.spyOn(selectors, "selectAuthentication").mockReturnValue({
      isAuthenticated: true,
      authenticating: false,
      error: null,
      tokenRefreshed: false,
      idToken: undefined,
      token: "test-token",
    });

    renderWithProviders();

    expect(screen.getByText("Protected")).toBeInTheDocument();
  });

  it("renders children when not authenticated and offline", () => {
    vi.spyOn(capacitor.Capacitor, "getPlatform").mockReturnValue("web");
    vi.spyOn(selectors, "selectAuthentication").mockReturnValue({
      isAuthenticated: false,
      authenticating: false,
      error: null,
      tokenRefreshed: false,
      idToken: undefined,
      token: "test-token",
    });
    vi.spyOn(selectors, "selectNetworkStatus").mockReturnValue({
      networkStatus: { connected: false, connectionType: "wifi" },
    });

    renderWithProviders();

    expect(screen.getByText("Protected")).toBeInTheDocument();
  });

  it("renders login button when online, unauthenticated and not authenticating", () => {
    vi.spyOn(capacitor.Capacitor, "getPlatform").mockReturnValue("web");
    vi.spyOn(selectors, "selectAuthentication").mockReturnValue({
      isAuthenticated: false,
      authenticating: false,
      error: null,
      tokenRefreshed: false,
      idToken: undefined,
      token: "test-token",
    });
    vi.spyOn(selectors, "selectNetworkStatus").mockReturnValue({
      networkStatus: { connected: true, connectionType: "wifi" },
    });

    renderWithProviders();

    expect(screen.getByText("Login")).toBeInTheDocument();
  });

  it("renders app description and title when unauthenticated and not authenticating", () => {
    vi.spyOn(capacitor.Capacitor, "getPlatform").mockReturnValue("web");
    vi.spyOn(selectors, "selectAuthentication").mockReturnValue({
      isAuthenticated: false,
      authenticating: false,
      error: null,
      tokenRefreshed: false,
      idToken: undefined,
      token: "test-token",
    });
    vi.spyOn(selectors, "selectNetworkStatus").mockReturnValue({
      networkStatus: { connected: true, connectionType: "wifi" },
    });

    renderWithProviders();

    expect(screen.getByText("ASA Go")).toBeInTheDocument();
    const description = screen.getByTestId("app-description");
    expect(description).toBeInTheDocument();
  });

  it("renders loading spinner when authenticating", () => {
    vi.spyOn(capacitor.Capacitor, "getPlatform").mockReturnValue("web");
    vi.spyOn(selectors, "selectAuthentication").mockReturnValue({
      isAuthenticated: false,
      authenticating: true,
      error: null,
      tokenRefreshed: false,
      idToken: undefined,
      token: "test-token",
    });
    vi.spyOn(selectors, "selectNetworkStatus").mockReturnValue({
      networkStatus: { connected: true, connectionType: "wifi" },
    });

    renderWithProviders();

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("renders error message when login fails", () => {
    vi.spyOn(capacitor.Capacitor, "getPlatform").mockReturnValue("web");
    vi.spyOn(selectors, "selectAuthentication").mockReturnValue({
      isAuthenticated: false,
      authenticating: false,
      error: "Invalid credentials",
      tokenRefreshed: false,
      idToken: undefined,
      token: "test-token",
    });
    vi.spyOn(selectors, "selectNetworkStatus").mockReturnValue({
      networkStatus: { connected: true, connectionType: "wifi" },
    });

    renderWithProviders();

    expect(
      screen.getByText("Unable to login, please try again.")
    ).toBeInTheDocument();
  });
});
