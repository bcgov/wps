import { describe, it, expect, vi, Mock } from "vitest";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import Settings from "./Settings";
import settingsReducer from "@/slices/settingsSlice";
import networkStatusReducer from "@/slices/networkStatusSlice";
import { FireCentreInfo, getFireCentreInfo } from "@/api/fbaAPI";
import * as Storage from "@/utils/storage";
import { NavPanel } from "@/utils/constants";

// Mock the API call
vi.mock("@/api/fbaAPI", async () => {
  const actual = await vi.importActual("@/api/fbaAPI");
  return {
    ...actual,
    getFireCentreInfo: vi.fn(),
  };
});

// Mock the @capacitor-firebase/messaging plugin
vi.mock("@capacitor-firebase/messaging", () => {
  const mockCheckPermissions = vi.fn().mockResolvedValue({ receive: "denied" });
  return {
    FirebaseMessaging: {
      checkPermissions: mockCheckPermissions,
    },
  };
});

vi.mock("@/utils/storage", async () => {
  const actual = await vi.importActual<typeof import("@/utils/storage")>(
    "@/utils/storage",
  );
  return {
    ...actual,
    readFromFilesystem: vi.fn(),
    writeToFileSystem: vi.fn(),
  };
});

// Mock data
const mockFireCentreInfos: FireCentreInfo[] = [
  {
    fire_centre_name: "Kamloops",
    fire_zone_units: [
      { id: 1, name: "Kamloops Zone 1" },
      { id: 2, name: "Kamloops Zone 2" },
    ],
  },
  {
    fire_centre_name: "Prince George",
    fire_zone_units: [
      { id: 3, name: "Prince George Zone 1" },
      { id: 4, name: "Prince George Zone 2" },
    ],
  },
];

// Create a mock store with the settings and network status slices
const createTestStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      settings: settingsReducer,
      networkStatus: networkStatusReducer,
    },
    preloadedState: initialState,
  });
};

describe("Settings", () => {
  // Mock the API call before each test
  beforeEach(() => {
    (getFireCentreInfo as Mock).mockResolvedValue({
      fire_centre_info: mockFireCentreInfos,
    });
    (Storage.readFromFilesystem as Mock).mockResolvedValue(null);
  });

  it("renders the settings component correctly", async () => {
    const store = createTestStore({
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
    });

    render(
      <Provider store={store}>
        <Settings activeTab={NavPanel.SETTINGS} />
      </Provider>,
    );

    expect(screen.getByTestId("asa-go-settings")).toBeInTheDocument();
  });

  it("renders fire centre accordions when data is loaded", async () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        fireCentreInfos: mockFireCentreInfos,
      },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
    });

    // Mock permission check to return granted immediately
    const { FirebaseMessaging } = await import("@capacitor-firebase/messaging");
    (FirebaseMessaging.checkPermissions as Mock).mockResolvedValue({
      receive: "granted",
    });

    render(
      <Provider store={store}>
        <Settings activeTab={NavPanel.SETTINGS} />
      </Provider>,
    );
    const fireCentreElements = await screen.findAllByRole("heading");
    expect(fireCentreElements[0]).toHaveTextContent(/KAMLOOPS/i);
    expect(fireCentreElements[1]).toHaveTextContent(/PRINCE GEORGE/i);
  });

  it("renders offline message when offline", async () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        fireCentreInfos: mockFireCentreInfos,
      },
      networkStatus: {
        networkStatus: { connected: false, connectionType: "none" },
      },
    });

    render(
      <Provider store={store}>
        <Settings activeTab={NavPanel.SETTINGS} />
      </Provider>,
    );
    expect(
      await screen.findByText(
        /Notification settings are not available while offline/i,
      ),
    ).toBeInTheDocument();
  });

  it("renders notification permission warning when permission is denied", async () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        fireCentreInfos: mockFireCentreInfos,
      },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
    });

    // Mock permission check to return denied
    const { FirebaseMessaging } = await import("@capacitor-firebase/messaging");
    (FirebaseMessaging.checkPermissions as Mock).mockResolvedValue({
      receive: "denied",
    });

    render(
      <Provider store={store}>
        <Settings activeTab={NavPanel.SETTINGS} />
      </Provider>,
    );
    expect(
      await screen.findByTestId("notifications-permission-warning"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Push notifications disabled/i),
    ).toBeInTheDocument();
  });

  it("renders notification prompt when permission is granted and online", async () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        fireCentreInfos: mockFireCentreInfos,
      },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
    });

    // Mock permission check to return granted
    const { FirebaseMessaging } = await import("@capacitor-firebase/messaging");
    (FirebaseMessaging.checkPermissions as Mock).mockResolvedValue({
      receive: "granted",
    });

    render(
      <Provider store={store}>
        <Settings activeTab={NavPanel.SETTINGS} />
      </Provider>,
    );
    expect(
      await screen.findByText(/Set your notification subscriptions/i),
    ).toBeInTheDocument();
  });

  it("renders accordions in sorted order with pinned fire centre first", async () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        fireCentreInfos: mockFireCentreInfos,
        pinnedFireCentre: "Prince George",
      },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
    });

    // Mock permission check to return granted
    const { FirebaseMessaging } = await import("@capacitor-firebase/messaging");
    (FirebaseMessaging.checkPermissions as Mock).mockResolvedValue({
      receive: "granted",
    });

    render(
      <Provider store={store}>
        <Settings activeTab={NavPanel.SETTINGS} />
      </Provider>,
    );
    // Check if pinned fire centre is first
    const fireCentreElements = await screen.findAllByRole("heading");
    expect(fireCentreElements[0]).toHaveTextContent(/PRINCE GEORGE/i);
  });

  it("renders loading state when loading is true", async () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        loading: true,
        fireCentreInfos: [],
      },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
    });

    render(
      <Provider store={store}>
        <Settings activeTab={NavPanel.SETTINGS} />
      </Provider>,
    );

    expect(
      screen.getByText(/Retrieving notification settings/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("renders error state when error is present", async () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        loading: false,
        error: "Failed to fetch fire centre info",
        fireCentreInfos: [],
      },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
    });

    render(
      <Provider store={store}>
        <Settings activeTab={NavPanel.SETTINGS} />
      </Provider>,
    );

    expect(screen.getByTestId("settings-error-alert")).toBeInTheDocument();
    expect(
      screen.getByText(
        /An error occurred when attempting to retrieve notification settings/i,
      ),
    ).toBeInTheDocument();
  });
});
