import { FireShape } from "@/api/fbaAPI";
import { useIsPortrait } from "@/hooks/useIsPortrait";
import { useIsTablet } from "@/hooks/useIsTablet";
import FireShapeActionsDrawer from "@/components/map/FireShapeActionsDrawer";
import { createTestStore } from "@/testUtils";
import { useMediaQuery } from "@mui/material";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import { describe, expect, it, vi, beforeEach, Mock } from "vitest";
import {
  getNotificationSettings,
  updateNotificationSettings,
} from "api/pushNotificationsAPI";
import { useDeviceId } from "@/hooks/useDeviceId";
import { FirebaseMessaging } from "@capacitor-firebase/messaging";
vi.mock("@/hooks/useDeviceId", () => ({
  useDeviceId: vi.fn().mockReturnValue("test-device-id"),
}));

vi.mock("@mui/material", async () => {
  const actual =
    await vi.importActual<typeof import("@mui/material")>("@mui/material");

  return {
    ...actual,
    useMediaQuery: vi.fn(),
  };
});

vi.mock("api/pushNotificationsAPI", () => ({
  getNotificationSettings: vi.fn().mockResolvedValue([]),
  registerToken: vi.fn().mockResolvedValue(undefined),
  updateNotificationSettings: vi.fn().mockResolvedValue([]),
}));

vi.mock("@/utils/retryWithBackoff", () => ({
  retryWithBackoff: vi.fn((op: () => Promise<unknown>) => op()),
}));

vi.mock("@capacitor/preferences", () => ({
  Preferences: {
    get: vi.fn().mockResolvedValue({ value: null }),
    set: vi.fn().mockResolvedValue(undefined),
  },
}));

vi.mock("@capacitor-firebase/messaging", () => ({
  FirebaseMessaging: {
    checkPermissions: vi.fn().mockResolvedValue({ receive: "granted" }),
    getToken: vi.fn().mockResolvedValue({ token: "test-token" }),
  },
}));

vi.mock("@/hooks/useIsPortrait", () => ({
  useIsPortrait: vi.fn(),
}));

vi.mock("@/hooks/useIsTablet", () => ({
  useIsTablet: vi.fn(),
}));

const mockFireShape: FireShape = {
  mof_fire_zone_name: "Test Fire Zone",
  fire_shape_id: 1,
  mof_fire_centre_name: "Test Fire Centre",
};

const theme = createTheme();

const renderWithProviders = ({
  subscriptions = [],
  pushNotificationPermission = "granted",
  connected = true,
  registeredFcmToken = "test-token",
  deviceIdError = false,
}: {
  subscriptions?: number[];
  pushNotificationPermission?: "granted" | "denied" | "prompt" | "unknown";
  connected?: boolean;
  registeredFcmToken?: string | null;
  deviceIdError?: boolean;
} = {}) => {
  const store = createTestStore({
    networkStatus: {
      networkStatus: {
        connected,
        connectionType: connected ? "wifi" : "none",
      },
    },
    settings: {
      loading: false,
      error: null,
      fireCentreInfos: [],
      pinnedFireCentre: null,
      subscriptions,
      subscriptionsInitialized: true,
    },
    pushNotification: {
      pushNotificationPermission,
      registeredFcmToken,
      deviceIdError,
      registrationError: false,
    },
  });

  render(
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <FireShapeActionsDrawer
          open
          selectedFireShape={mockFireShape}
          onClose={vi.fn()}
          onSelectProfile={vi.fn()}
          onSelectAdvisory={vi.fn()}
        />
      </ThemeProvider>
    </Provider>,
  );
  return { store };
};

describe("FireShapeActionsDrawer", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({
      token: "test-token",
    });
    vi.mocked(useDeviceId).mockReturnValue("test-device-id");
    vi.mocked(getNotificationSettings).mockResolvedValue([]);
    vi.mocked(updateNotificationSettings).mockImplementation((_, subs) =>
      Promise.resolve(subs),
    );
    vi.mocked(useIsPortrait).mockReturnValue(true);
    vi.mocked(useIsTablet).mockReturnValue(false);
    vi.mocked(useMediaQuery).mockReturnValue(false);
  });

  it("renders the selected fire shape name and action buttons", () => {
    renderWithProviders();

    expect(screen.getByText("Test Fire")).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Subscribe")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Profile" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Advisory" }),
    ).toBeInTheDocument();
  });

  it("calls onClose from the close button", () => {
    const onClose = vi.fn();
    const store = createTestStore({
      networkStatus: {
        networkStatus: {
          connected: true,
          connectionType: "wifi",
        },
      },
      settings: {
        loading: false,
        error: null,
        fireCentreInfos: [],
        pinnedFireCentre: null,
        subscriptions: [],
        subscriptionsInitialized: false,
      },
      pushNotification: {
        pushNotificationPermission: "granted",
        registeredFcmToken: null,
        deviceIdError: false,
        registrationError: false,
      },
    });
    const theme = createTheme();

    render(
      <Provider store={store}>
        <ThemeProvider theme={theme}>
          <FireShapeActionsDrawer
            open
            selectedFireShape={mockFireShape}
            onClose={onClose}
            onSelectProfile={vi.fn()}
            onSelectAdvisory={vi.fn()}
          />
        </ThemeProvider>
      </Provider>,
    );

    fireEvent.click(screen.getByTestId("fire-shape-drawer-close-button"));

    expect(onClose).toHaveBeenCalled();
  });

  it("calls the navigation callbacks", () => {
    const onSelectProfile = vi.fn();
    const onSelectAdvisory = vi.fn();
    const store = createTestStore({
      networkStatus: {
        networkStatus: {
          connected: true,
          connectionType: "wifi",
        },
      },
      settings: {
        loading: false,
        error: null,
        fireCentreInfos: [],
        pinnedFireCentre: null,
        subscriptions: [],
        subscriptionsInitialized: false,
      },
      pushNotification: {
        pushNotificationPermission: "granted",
        registeredFcmToken: null,
        deviceIdError: false,
        registrationError: false,
      },
    });
    const theme = createTheme();

    render(
      <Provider store={store}>
        <ThemeProvider theme={theme}>
          <FireShapeActionsDrawer
            open
            selectedFireShape={mockFireShape}
            onClose={vi.fn()}
            onSelectProfile={onSelectProfile}
            onSelectAdvisory={onSelectAdvisory}
          />
        </ThemeProvider>
      </Provider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Profile" }));
    fireEvent.click(screen.getByRole("button", { name: "Advisory" }));

    expect(onSelectProfile).toHaveBeenCalled();
    expect(onSelectAdvisory).toHaveBeenCalled();
  });

  it("toggles the subscription for the selected fire shape", async () => {
    const { store } = renderWithProviders();
    fireEvent.click(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    );

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual([1]);
    });
    expect(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    ).toHaveTextContent("Unsubscribe");
  });

  it("shows the subscribed state when already subscribed", () => {
    renderWithProviders({ subscriptions: [1] });

    expect(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Unsubscribe")).toBeInTheDocument();
  });

  it("disables subscription when notifications are unavailable", () => {
    renderWithProviders({ pushNotificationPermission: "denied" });

    expect(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    ).toBeDisabled();
  });

  it("disables subscription when awaiting FCM token", () => {
    renderWithProviders({ registeredFcmToken: null });

    expect(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    ).toBeDisabled();
  });

  it("uses the side-sheet layout on landscape small screens", async () => {
    vi.mocked(useIsPortrait).mockReturnValue(false);
    vi.mocked(useMediaQuery).mockReturnValue(true);

    renderWithProviders();

    const actionGrid = screen.getByRole("button", {
      name: /Toggle subscription for Test Fire Zone/i,
    }).parentElement?.parentElement;

    expect(actionGrid).toHaveStyle({
      gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    });

    await waitFor(() => {
      expect(document.querySelector(".MuiDrawer-paper")).toHaveStyle({
        left: theme.spacing(1),
        right: "auto",
        bottom: 0,
        width: "min(320px, 78vw)",
      });
    });
  });

  it("keeps the standard bottom-sheet layout outside landscape small screens", async () => {
    renderWithProviders();

    const actionGrid = screen.getByRole("button", {
      name: /Toggle subscription for Test Fire Zone/i,
    }).parentElement?.parentElement;

    expect(actionGrid).toHaveStyle({
      gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
    });

    await waitFor(() => {
      expect(document.querySelector(".MuiDrawer-paper")).toHaveStyle({
        left: "0px",
        right: "0px",
        bottom: "0px",
      });
    });
  });

  it("uses the tablet icon size when the device is tablet-sized", () => {
    vi.mocked(useIsTablet).mockReturnValue(true);

    renderWithProviders();

    expect(screen.getByTestId("AnalyticsIcon")).toHaveStyle({
      fontSize: "40px",
    });
  });

  it("calls updateNotificationSettings when toggling subscription", async () => {
    renderWithProviders();
    fireEvent.click(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    );

    await waitFor(() => {
      expect(updateNotificationSettings).toHaveBeenCalledWith(
        "test-device-id",
        ["1"],
      );
    });
  });

  it("updates store from server response after toggling", async () => {
    // Server returns a corrected list (e.g. deduped or reordered)
    (updateNotificationSettings as Mock).mockResolvedValue(["1", "99"]);

    const { store } = renderWithProviders();
    fireEvent.click(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    );

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual([1, 99]);
    });
  });

  it("reverts local state when the server call fails", async () => {
    (updateNotificationSettings as Mock).mockRejectedValue(
      new Error("server error"),
    );
    (getNotificationSettings as Mock).mockResolvedValue(["42"]);

    const { store } = renderWithProviders({ subscriptions: [42] });
    fireEvent.click(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    );

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual([42]);
    });
  });

  it("shows error snackbar when subscription toggle fails", async () => {
    vi.mocked(updateNotificationSettings).mockRejectedValue(
      new Error("server error"),
    );
    vi.spyOn(console, "error").mockImplementation(() => {});

    renderWithProviders();
    fireEvent.click(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to update/i)).toBeInTheDocument();
    });
  });

  it("shows a loading spinner on the subscribe button when awaiting FCM token", () => {
    renderWithProviders({ registeredFcmToken: null });
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("disables the subscribe button when permission is denied", () => {
    renderWithProviders({ pushNotificationPermission: "denied" });
    expect(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    ).toBeDisabled();
  });

  it("disables the subscribe button when offline", () => {
    renderWithProviders({ connected: false });
    expect(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    ).toBeDisabled();
  });

  it("disables the subscribe button when device ID error", () => {
    renderWithProviders({ deviceIdError: true, registeredFcmToken: null });
    expect(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    ).toBeDisabled();
  });

  it("does not call updateNotificationSettings when offline", async () => {
    renderWithProviders({
      connected: false,
      pushNotificationPermission: "granted",
    });

    // Button is disabled when offline, so no click possible — just verify the API is never called
    expect(
      screen.getByRole("button", {
        name: /Toggle subscription for Test Fire Zone/i,
      }),
    ).toBeDisabled();
    expect(updateNotificationSettings).not.toHaveBeenCalled();
  });
});
