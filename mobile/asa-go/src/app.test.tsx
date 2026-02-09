import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import App from "./App";
import { Provider } from "react-redux";
import { createTestStore } from "./testUtils";
import { NavPanel } from "@/utils/constants";

// Mock Capacitor plugins
vi.mock("@capacitor/screen-orientation", () => ({
  ScreenOrientation: {
    addListener: vi.fn(),
    removeAllListeners: vi.fn(),
    orientation: vi.fn().mockResolvedValue({ type: "portrait-primary" }),
  },
}));

vi.mock("@capacitor/status-bar", () => ({
  StatusBar: {
    show: vi.fn(),
    hide: vi.fn(),
  },
}));

vi.mock("@capacitor/network", () => ({
  Network: {
    getStatus: vi
      .fn()
      .mockResolvedValue({ connected: true, connectionType: "wifi" }),
    addListener: vi.fn(),
    removeAllListeners: vi.fn(),
  },
}));

vi.mock("@capacitor/filesystem", () => ({
  Filesystem: {},
}));

// Mock components
vi.mock("@/components/AppHeader", () => ({
  AppHeader: () => <div data-testid="app-header">App Header</div>,
}));

vi.mock("@/components/BottomNavigationBar", () => ({
  default: ({ tab }: { tab: NavPanel; setTab: (tab: NavPanel) => void }) => (
    <div data-testid="bottom-nav">Bottom Nav: {tab}</div>
  ),
}));

vi.mock("@/components/map/ASAGoMap", () => ({
  default: () => <div data-testid="asa-go-map">ASA Go Map</div>,
}));

vi.mock("@/components/profile/Profile", () => ({
  default: () => <div data-testid="profile">Profile</div>,
}));

vi.mock("@/components/report/Advisory", () => ({
  default: () => <div data-testid="advisory">Advisory</div>,
}));

vi.mock("@/components/TabPanel", () => ({
  default: ({
    value,
    panel,
    children,
  }: {
    value: NavPanel;
    panel: NavPanel;
    children: React.ReactNode;
  }) =>
    value === panel ? (
      <div data-testid={`tab-panel-${panel}`}>{children}</div>
    ) : null,
}));

vi.mock("@/components/SideNavigation", () => ({
  default: ({ tab }: { tab: NavPanel; setTab: (tab: NavPanel) => void }) => (
    <div data-testid="side-navigation">Side Navigation: {tab}</div>
  ),
}));

// Mock hooks
vi.mock("@/hooks/useAppIsActive", () => ({
  useAppIsActive: () => true,
}));

vi.mock("@/hooks/useRunParameterForDate", () => ({
  useRunParameterForDate: () => undefined,
}));

describe("App", () => {
  it("renders all main components in initial state", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <App />
      </Provider>,
    );

    // Check if AppHeader is rendered
    expect(screen.getByTestId("app-header")).toBeInTheDocument();

    // Check if BottomNavigationBar is rendered
    expect(screen.getByTestId("bottom-nav")).toBeInTheDocument();

    // Check if ASAGoMap is rendered (initial tab is MAP)
    expect(screen.getByTestId("asa-go-map")).toBeInTheDocument();
  });

  it("renders App component with Redux store integration", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <App />
      </Provider>,
    );

    // Verify the app container is present
    const appContainer = document.getElementById("asa-go-app");
    expect(appContainer).toBeInTheDocument();
  });

  it("initializes with correct styling", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <App />
      </Provider>,
    );

    const appContainer = document.getElementById("asa-go-app");
    expect(appContainer).toHaveStyle({
      height: "100vh",
      padding: "0",
      margin: "0",
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
    });
  });

  it("hides AppHeader and calls StatusBar.hide() when device is in landscape orientation", async () => {
    const { StatusBar } = await import("@capacitor/status-bar");
    const { ScreenOrientation } = await import("@capacitor/screen-orientation");

    // Mock landscape orientation
    const mockOrientation = vi
      .fn()
      .mockResolvedValue({ type: "landscape-primary" });
    ScreenOrientation.orientation = mockOrientation;

    const store = createTestStore();

    render(
      <Provider store={store}>
        <App />
      </Provider>,
    );

    // Wait for async orientation check to complete
    await waitFor(() => {
      expect(mockOrientation).toHaveBeenCalled();
    });

    // Check if StatusBar.hide() is called
    expect(StatusBar.hide).toHaveBeenCalled();
  });

  it("shows AppHeader and calls StatusBar.show() when device is in portrait orientation", async () => {
    const { StatusBar } = await import("@capacitor/status-bar");
    const { ScreenOrientation } = await import("@capacitor/screen-orientation");

    // Mock portrait orientation
    const mockOrientation = vi
      .fn()
      .mockResolvedValue({ type: "portrait-primary" });
    ScreenOrientation.orientation = mockOrientation;

    const store = createTestStore();

    render(
      <Provider store={store}>
        <App />
      </Provider>,
    );

    // Wait for async orientation check to complete
    await waitFor(() => {
      expect(mockOrientation).toHaveBeenCalled();
    });

    // Check if StatusBar.show() is called
    expect(StatusBar.show).toHaveBeenCalled();
  });

  it("displays SideNavigation and hides BottomNavigation in landscape on small screens", async () => {
    const { ScreenOrientation } = await import("@capacitor/screen-orientation");

    // Mock landscape orientation and small screen
    ScreenOrientation.orientation = vi
      .fn()
      .mockResolvedValue({ type: "landscape-primary" });

    const store = createTestStore();

    render(
      <Provider store={store}>
        <App />
      </Provider>,
    );

    // Wait for async orientation check to complete
    await waitFor(() => {
      expect(ScreenOrientation.orientation).toHaveBeenCalled();
    });

    // Check if SideNavigation is displayed and BottomNavigation is hidden on small screens
    expect(screen.getByTestId("side-navigation")).toBeInTheDocument();
    expect(screen.queryByTestId("bottom-nav")).not.toBeInTheDocument();
  });

  it("displays AppHeader and BottomNavigation in portrait on small screens", async () => {
    const { ScreenOrientation } = await import("@capacitor/screen-orientation");

    // Mock portrait orientation and small screen
    ScreenOrientation.orientation = vi
      .fn()
      .mockResolvedValue({ type: "portrait-primary" });

    const store = createTestStore();

    render(
      <Provider store={store}>
        <App />
      </Provider>,
    );

    // Wait for async orientation check to complete
    await waitFor(() => {
      expect(ScreenOrientation.orientation).toHaveBeenCalled();
    });

    // Check if AppHeader and BottomNavigation are displayed
    expect(screen.getByTestId("app-header")).toBeInTheDocument();
    expect(screen.getByTestId("bottom-nav")).toBeInTheDocument();
  });

  it("displays AppHeader and BottomNavigation in landscape on medium or larger screens", async () => {
    const { ScreenOrientation } = await import("@capacitor/screen-orientation");

    // Mock landscape orientation and medium/large screen
    ScreenOrientation.orientation = vi
      .fn()
      .mockResolvedValue({ type: "landscape-primary" });

    // Increase window width to be larger than md breakpoint (900px)
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 1024,
    });

    // Force reflow of media query listeners
    window.dispatchEvent(new Event("resize"));

    const store = createTestStore();

    render(
      <Provider store={store}>
        <App />
      </Provider>,
    );

    // Wait for async orientation check to complete
    await waitFor(() => {
      expect(ScreenOrientation.orientation).toHaveBeenCalled();
    });

    // Check if AppHeader and BottomNavigation are displayed
    expect(screen.getByTestId("app-header")).toBeInTheDocument();
    expect(screen.getByTestId("bottom-nav")).toBeInTheDocument();
    expect(screen.queryByTestId("side-navigation")).not.toBeInTheDocument();
  });

  it("displays AppHeader and BottomNavigation in portrait on medium or larger screens", async () => {
    const { ScreenOrientation } = await import("@capacitor/screen-orientation");

    // Mock portrait orientation and medium/large screen
    ScreenOrientation.orientation = vi
      .fn()
      .mockResolvedValue({ type: "portrait-primary" });

    // Increase window width to be larger than md breakpoint (900px)
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 1024,
    });

    // Force reflow of media query listeners
    window.dispatchEvent(new Event("resize"));

    const store = createTestStore();

    render(
      <Provider store={store}>
        <App />
      </Provider>,
    );

    // Wait for async orientation check to complete
    await waitFor(() => {
      expect(ScreenOrientation.orientation).toHaveBeenCalled();
    });

    // Check if AppHeader and BottomNavigation are displayed
    expect(screen.getByTestId("app-header")).toBeInTheDocument();
    expect(screen.getByTestId("bottom-nav")).toBeInTheDocument();
  });
});
