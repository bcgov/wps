import { FireShape } from "@/api/fbaAPI";
import { useIsPortrait } from "@/hooks/useIsPortrait";
import { useIsTablet } from "@/hooks/useIsTablet";
import FireShapeActionsDrawer from "@/components/map/FireShapeActionsDrawer";
import { createTestStore } from "@/testUtils";
import { Preferences } from "@capacitor/preferences";
import { useMediaQuery } from "@mui/material";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("@mui/material", async () => {
  const actual = await vi.importActual<typeof import("@mui/material")>(
    "@mui/material",
  );

  return {
    ...actual,
    useMediaQuery: vi.fn(),
  };
});

vi.mock("@capacitor/preferences", () => ({
  Preferences: {
    get: vi.fn().mockResolvedValue({ value: null }),
    set: vi.fn().mockResolvedValue(undefined),
  },
}));

vi.mock("@capacitor-firebase/messaging", () => ({
  FirebaseMessaging: {
    checkPermissions: vi.fn().mockResolvedValue({ receive: "granted" }),
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
}: {
  subscriptions?: number[];
  pushNotificationPermission?: "granted" | "denied" | "prompt" | "unknown";
  connected?: boolean;
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
      pushNotificationPermission,
      subscriptions,
    },
  });

  return {
    ...render(
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
    ),
    store,
  };
};

describe("FireShapeActionsDrawer", () => {
  beforeEach(() => {
    vi.resetAllMocks();
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
        pushNotificationPermission: "granted",
        subscriptions: [],
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
        pushNotificationPermission: "granted",
        subscriptions: [],
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
    expect(Preferences.set).toHaveBeenCalledWith({
      key: "asaGoSubscriptions",
      value: JSON.stringify([1]),
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

  it("uses the side-sheet layout on landscape small screens", async () => {
    vi.mocked(useIsPortrait).mockReturnValue(false);
    vi.mocked(useMediaQuery).mockReturnValue(true);

    renderWithProviders();

    const actionGrid = screen.getByRole("button", {
      name: /Toggle subscription for Test Fire Zone/i,
    }).parentElement;

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
    }).parentElement;

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
});
