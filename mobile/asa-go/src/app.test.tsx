import { act, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import App from "./App";
import { Provider } from "react-redux";
import { createTestStore } from "./testUtils";
import { NavPanel } from "@/utils/constants";
import { useMediaQuery } from "@mui/material";
import { usePushNotifications } from "@/hooks/usePushNotifications";
import { initialState as pushNotificationInitialState } from "@/slices/pushNotificationSlice";
import { RunType } from "@/api/fbaAPI";

// Mock MUI useMediaQuery to control screen size detection
vi.mock("@mui/material", async () => {
  const actual = await vi.importActual("@mui/material");
  return {
    ...actual,
    useMediaQuery: vi.fn(),
  };
});

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

vi.mock("@/hooks/usePushNotifications", () => ({
  usePushNotifications: vi.fn().mockReturnValue({
    initPushNotifications: vi.fn().mockResolvedValue(undefined),
    retryRegistration: vi.fn().mockResolvedValue(undefined),
    currentFcmToken: null,
  }),
}));

vi.mock("@capacitor/device", () => ({
  Device: { getId: vi.fn().mockResolvedValue({ identifier: "device-id" }) },
}));

vi.mock("@capacitor/core", () => ({
  Capacitor: { getPlatform: () => "ios" },
}));

vi.mock("@/api/pushNotificationsAPI", () => ({
  registerToken: vi.fn(),
  Platform: {},
}));

vi.mock("@/utils/dataSliceUtils", async () => {
  const actual = await vi.importActual("@/utils/dataSliceUtils");
  const { DateTime } = await vi.importActual<typeof import("luxon")>("luxon");
  return {
    ...actual,
    today: DateTime.fromISO("2025-07-02"),
  };
});

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(usePushNotifications).mockReturnValue({
      initPushNotifications: vi.fn().mockResolvedValue(undefined),
      retryRegistration: vi.fn().mockResolvedValue(undefined),
    });
  });

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

    // Mock landscape orientation
    ScreenOrientation.orientation = vi
      .fn()
      .mockResolvedValue({ type: "landscape-primary" });

    // Mock small screen
    vi.mocked(useMediaQuery).mockReturnValue(true);

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
    await waitFor(() =>
      expect(screen.getByTestId("side-navigation")).toBeInTheDocument(),
    );
    expect(screen.queryByTestId("bottom-nav")).not.toBeInTheDocument();
  });

  it("displays AppHeader and BottomNavigation in portrait on small screens", async () => {
    const { ScreenOrientation } = await import("@capacitor/screen-orientation");

    // Mock portrait orientation
    ScreenOrientation.orientation = vi
      .fn()
      .mockResolvedValue({ type: "portrait-primary" });

    // Mock small screen
    vi.mocked(useMediaQuery).mockReturnValue(true);

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

    // Mock landscape orientation
    ScreenOrientation.orientation = vi
      .fn()
      .mockResolvedValue({ type: "landscape-primary" });

    // Mock medium/large screen
    vi.mocked(useMediaQuery).mockReturnValue(false);

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

  it("calls initPushNotifications when authenticated", async () => {
    const initPushNotifications = vi.fn().mockResolvedValue(undefined);
    vi.mocked(usePushNotifications).mockReturnValue({
      initPushNotifications,
      retryRegistration: vi.fn().mockResolvedValue(undefined),
    });

    const store = createTestStore({
      authentication: {
        isAuthenticated: true,
        authenticating: false,
        tokenRefreshed: false,
        token: undefined,
        idToken: undefined,
        idir: undefined,
        error: null,
      },
    });

    await act(async () => {
      render(
        <Provider store={store}>
          <App />
        </Provider>,
      );
    });

    expect(initPushNotifications).toHaveBeenCalledTimes(1);
  });

  it("does not call initPushNotifications when not authenticated", async () => {
    const initPushNotifications = vi.fn().mockResolvedValue(undefined);
    vi.mocked(usePushNotifications).mockReturnValue({
      initPushNotifications,
      retryRegistration: vi.fn().mockResolvedValue(undefined),
    });

    const store = createTestStore();

    await act(async () => {
      render(
        <Provider store={store}>
          <App />
        </Provider>,
      );
    });

    expect(initPushNotifications).not.toHaveBeenCalled();
  });

  it("displays AppHeader and BottomNavigation in portrait on medium or larger screens", async () => {
    const { ScreenOrientation } = await import("@capacitor/screen-orientation");

    // Mock portrait orientation
    ScreenOrientation.orientation = vi
      .fn()
      .mockResolvedValue({ type: "portrait-primary" });

    // Mock medium/large screen
    vi.mocked(useMediaQuery).mockReturnValue(false);

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

  describe("pendingNotificationData effect", () => {
    const TODAY_ISO = "2025-07-02";
    const mockRunParameter = {
      for_date: TODAY_ISO,
      run_datetime: `${TODAY_ISO}T12:00:00`,
      run_type: RunType.FORECAST,
    };
    const mockFireCentre = { id: 1, name: "Cariboo" };
    const mockFireShape = {
      fire_shape_id: 42,
      fire_shape_name: "Zone 1",
      fire_centre_name: "Cariboo",
      status: null,
    };

    const buildStore = (
      overrides: {
        advisory_date?: string;
        fire_centre_id?: string;
        fire_zone_unit?: string;
        fireCentreId?: number;
        fireShapeId?: number;
      } = {},
    ) => {
      const {
        advisory_date = TODAY_ISO,
        fire_centre_id = "1",
        fire_zone_unit = "42",
        fireCentreId = 1,
        fireShapeId = 42,
      } = overrides;

      return createTestStore({
        pushNotification: {
          ...pushNotificationInitialState,
          pendingNotificationData: {
            advisory_date,
            fire_centre_id,
            fire_zone_unit,
          },
        },
        fireCentres: {
          loading: false,
          error: null,
          fireCentres: [{ id: fireCentreId, name: mockFireCentre.name }],
        },
        data: {
          loading: false,
          error: null,
          lastUpdated: null,
          provincialSummaries: {
            [TODAY_ISO]: {
              runParameter: mockRunParameter,
              data: [{ ...mockFireShape, fire_shape_id: fireShapeId }],
            },
          },
          tpiStats: null,
          hfiStats: null,
        },
      });
    };

    it("does not navigate when advisory_date does not match today", async () => {
      const store = buildStore({ advisory_date: "2024-01-01" });

      await act(async () => {
        render(
          <Provider store={store}>
            <App />
          </Provider>,
        );
      });

      expect(screen.getByTestId("asa-go-map")).toBeInTheDocument();
      expect(screen.queryByTestId("advisory")).not.toBeInTheDocument();
      expect(
        store.getState().pushNotification.pendingNotificationData,
      ).not.toBeNull();
    });

    it("does not navigate when fire centre is not found", async () => {
      const store = buildStore({ fire_centre_id: "999" });

      await act(async () => {
        render(
          <Provider store={store}>
            <App />
          </Provider>,
        );
      });

      expect(screen.getByTestId("asa-go-map")).toBeInTheDocument();
      expect(screen.queryByTestId("advisory")).not.toBeInTheDocument();
      expect(
        store.getState().pushNotification.pendingNotificationData,
      ).not.toBeNull();
    });

    it("does not navigate when fire shape is not found in provincialSummaries", async () => {
      const store = buildStore({ fire_zone_unit: "999" });

      await act(async () => {
        render(
          <Provider store={store}>
            <App />
          </Provider>,
        );
      });

      expect(screen.getByTestId("asa-go-map")).toBeInTheDocument();
      expect(screen.queryByTestId("advisory")).not.toBeInTheDocument();
      expect(
        store.getState().pushNotification.pendingNotificationData,
      ).not.toBeNull();
    });

    it("navigates to Advisory tab and clears pendingNotificationData when all data resolves", async () => {
      const store = buildStore();

      await act(async () => {
        render(
          <Provider store={store}>
            <App />
          </Provider>,
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId("advisory")).toBeInTheDocument();
      });

      expect(screen.queryByTestId("asa-go-map")).not.toBeInTheDocument();
      expect(
        store.getState().pushNotification.pendingNotificationData,
      ).toBeNull();
    });
  });
});
