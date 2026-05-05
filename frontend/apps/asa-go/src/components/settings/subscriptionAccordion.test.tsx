import { FireCentreInfo } from "@/api/fbaAPI";
import settingsReducer from "@/slices/settingsSlice";
import { createTestStore } from "@/testUtils";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";

import { Provider } from "react-redux";
import { describe, expect, it, vi, beforeEach } from "vitest";
import SubscriptionAccordion from "@/components/settings/SubscriptionAccordion";
vi.mock("@/hooks/useDeviceId", () => ({
  useDeviceId: vi.fn().mockReturnValue("test-device-id"),
}));

vi.mock("api/pushNotificationsAPI", () => ({
  getNotificationSettings: vi.fn(),
  updateNotificationSettings: vi.fn(),
  registerToken: vi.fn(),
}));

vi.mock("@/utils/retryWithBackoff", () => ({
  retryWithBackoff: vi.fn((op: () => Promise<unknown>) => op()),
}));

import {
  getNotificationSettings,
  updateNotificationSettings,
} from "api/pushNotificationsAPI";
import { subscriptionUpdateErrorMessage } from "@/utils/constants";

vi.mock("@capacitor/preferences", () => ({
  Preferences: {
    get: vi.fn().mockResolvedValue({ value: null }),
    set: vi.fn().mockResolvedValue(undefined),
    remove: vi.fn().mockResolvedValue(undefined),
  },
}));

const FIRE_CENTRE_LABEL = "KAMLOOPS";
const VERNON_ZONE_LABEL = "K4-Vernon";
const LILLOOET_ZONE_LABEL = "K7-Lillooet";

const getZoneLabel = (label: string) =>
  screen.getByText((_, element) => {
    return element?.tagName === "P" && element.textContent === label;
  });

const queryZoneLabel = (label: string) =>
  screen.queryByText((_, element) => {
    return element?.tagName === "P" && element.textContent === label;
  });

const getAccordionButton = () =>
  screen.getByText(FIRE_CENTRE_LABEL).closest("button");

const getAccordion = (fireCentreName: string) =>
  screen.getByLabelText(`accordion-${fireCentreName}`);

const getAllCheckbox = (fireCentreName: string) =>
  within(getAccordion(fireCentreName)).getByLabelText("All");

const getPinButton = () => {
  const pinButton = within(getAccordion("Kamloops Fire Centre"))
    .getAllByRole("button")
    .find((button) => !button.getAttribute("aria-controls"));

  expect(pinButton).toBeDefined();
  return pinButton as HTMLElement;
};

const mockFireCentreInfo: FireCentreInfo = {
  fire_centre_name: "Kamloops Fire Centre",
  fire_zone_units: [
    { id: 10, name: "K4-Vernon Zone (Vernon)" },
    { id: 12, name: "K7-Lillooet Zone" },
    { id: 16, name: "K2-Kamloops Zone (Kamloops)" },
    { id: 5, name: "K5-Penticton Zone" },
    { id: 6, name: "K6-Merritt Zone" },
  ],
};
const KAMLOOPS_FIRE_ZONE_IDS = mockFireCentreInfo.fire_zone_units.map(
  (fireZoneUnit) => fireZoneUnit.id,
);

const mockFireCentreInfos: FireCentreInfo[] = [
  {
    fire_centre_name: "Kamloops",
    fire_zone_units: [
      { id: 16, name: "K2-Kamloops Zone (Kamloops)" },
      { id: 5, name: "K5-Penticton Zone" },
    ],
  },
  {
    fire_centre_name: "Prince George",
    fire_zone_units: [
      { id: 3, name: "G1-Prince George Zone" },
      { id: 4, name: "G3-Robson Valley Zone" },
    ],
  },
];

const createConnectedStore = (
  settingsOverrides: Partial<ReturnType<typeof settingsReducer>> = {},
) =>
  createTestStore({
    pushNotification: {
      pushNotificationPermission: "granted" as const,
      registeredFcmToken: "test-token",
      deviceIdError: false,
      registrationError: false,
      registrationAttempts: 0,
      pendingNotificationData: null,
    },
    networkStatus: {
      networkStatus: { connected: true, connectionType: "wifi" },
    },
    settings: {
      ...settingsReducer(undefined, { type: "unknown" }),
      loading: false,
      error: null,
      fireCentreInfos: [],
      pinnedFireCentre: null,
      subscriptions: [],
      subscriptionsInitialized: true,
      ...settingsOverrides,
    },
  });

interface RenderAccordionOptions {
  store?: ReturnType<typeof createTestStore>;
  fireCentreInfo?: FireCentreInfo;
  defaultExpanded?: boolean;
  disabled?: boolean;
}

const renderAccordion = ({
  store = createTestStore(),
  fireCentreInfo = mockFireCentreInfo,
  defaultExpanded = false,
  disabled = false,
}: RenderAccordionOptions = {}) =>
  render(
    <Provider store={store}>
      <SubscriptionAccordion
        disabled={disabled}
        fireCentreInfo={fireCentreInfo}
        defaultExpanded={defaultExpanded}
      />
    </Provider>,
  );

describe("SubscriptionAccordion", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getNotificationSettings).mockResolvedValue([]);
    vi.mocked(updateNotificationSettings).mockImplementation((_, subs) =>
      Promise.resolve(subs),
    );
  });

  it("renders correctly with fire centre name", () => {
    renderAccordion();
    expect(screen.getByText(FIRE_CENTRE_LABEL)).toBeInTheDocument();
  });

  it("renders as expanded when defaultExpanded is true", () => {
    renderAccordion({ defaultExpanded: true });
    expect(getZoneLabel(LILLOOET_ZONE_LABEL)).toBeInTheDocument();
    expect(getZoneLabel(VERNON_ZONE_LABEL)).toBeInTheDocument();
  });

  it("renders as collapsed when defaultExpanded is false", () => {
    renderAccordion();
    expect(getZoneLabel(LILLOOET_ZONE_LABEL)).not.toBeVisible();
    expect(getZoneLabel(VERNON_ZONE_LABEL)).not.toBeVisible();
  });

  it("renders all fire zone units as SubscriptionOptions", () => {
    renderAccordion();
    fireEvent.click(getAccordionButton() as HTMLElement);
    expect(getZoneLabel(LILLOOET_ZONE_LABEL)).toBeInTheDocument();
    expect(getZoneLabel(VERNON_ZONE_LABEL)).toBeInTheDocument();
  });

  it("expands and collapses when clicked", async () => {
    renderAccordion({ store: createConnectedStore() });

    expect(getZoneLabel(LILLOOET_ZONE_LABEL)).not.toBeVisible();
    expect(getZoneLabel(VERNON_ZONE_LABEL)).not.toBeVisible();

    fireEvent.click(getAccordionButton() as HTMLElement);
    expect(getZoneLabel(LILLOOET_ZONE_LABEL)).toBeVisible();
    expect(getZoneLabel(VERNON_ZONE_LABEL)).toBeVisible();

    fireEvent.click(getAccordionButton() as HTMLElement);
    await waitFor(() => {
      expect(queryZoneLabel(LILLOOET_ZONE_LABEL)).not.toBeVisible();
      expect(queryZoneLabel(VERNON_ZONE_LABEL)).not.toBeVisible();
    });
  });

  it("is disabled when disabled prop is true", () => {
    renderAccordion({ disabled: true });

    const accordion = getAccordionButton()?.closest(".MuiAccordion-root");
    expect(accordion).toHaveStyle({ opacity: "0.5", filter: "grayscale(1)" });

    const checkbox = within(accordion as HTMLElement).getByRole("checkbox");
    expect(checkbox).toBeDisabled();

    fireEvent.click(getAccordionButton() as HTMLElement);
    expect(getZoneLabel(LILLOOET_ZONE_LABEL)).not.toBeVisible();
    expect(getZoneLabel(VERNON_ZONE_LABEL)).not.toBeVisible();

    const toggleSwitches = within(accordion as HTMLElement).getAllByTestId(
      "loading-switch",
    );
    toggleSwitches.forEach((toggleSwitch) => {
      expect(toggleSwitch).toHaveClass("Mui-disabled");
    });
  });

  it("shows a snackbar error when a subscription toggle fails", async () => {
    vi.mocked(updateNotificationSettings).mockRejectedValue(
      new Error("server error"),
    );
    vi.spyOn(console, "error").mockImplementation(() => {});

    const store = createConnectedStore({ fireCentreInfos: [mockFireCentreInfo] });
    renderAccordion({ store, defaultExpanded: true });

    const firstZone = mockFireCentreInfo.fire_zone_units[0];
    await act(async () => {
      fireEvent.click(
        screen.getByLabelText(`Toggle subscription for ${firstZone.name}`),
      );
    });

    expect(updateNotificationSettings).toHaveBeenCalled();
    expect(screen.getByText(subscriptionUpdateErrorMessage)).toBeInTheDocument();
    expect(screen.queryAllByTestId("loading-switch-error")).toHaveLength(0);
  });

  it("displays filled push pin icon when fire centre is pinned", () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        pinnedFireCentre: mockFireCentreInfo.fire_centre_name,
      },
    });
    renderAccordion({ store });
    expect(getPinButton()).toBeInTheDocument();
  });

  it("displays outlined push pin icon when fire centre is not pinned", () => {
    renderAccordion();
    expect(getPinButton()).toBeInTheDocument();
  });

  it("pins the fire centre when pin button is clicked and not already pinned", async () => {
    const store = createTestStore();
    renderAccordion({ store });
    fireEvent.click(getPinButton());
    await waitFor(() => {
      expect(store.getState().settings.pinnedFireCentre).toEqual(
        mockFireCentreInfo.fire_centre_name,
      );
    });
  });

  it("unpins the fire centre when pin button is clicked and already pinned", async () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        pinnedFireCentre: mockFireCentreInfo.fire_centre_name,
      },
    });
    renderAccordion({ store });
    fireEvent.click(getPinButton());
    await waitFor(() => {
      expect(store.getState().settings.pinnedFireCentre).toBeNull();
    });
  });

  it("selects all fire zone units when 'All' checkbox is checked", async () => {
    const store = createConnectedStore();
    await act(async () => renderAccordion({ store, defaultExpanded: true }));
    fireEvent.click(getAllCheckbox("Kamloops Fire Centre"));
    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual(
        KAMLOOPS_FIRE_ZONE_IDS,
      );
    });
  });

  it("deselects all fire zone units when 'All' checkbox is unchecked", async () => {
    const store = createConnectedStore({ subscriptions: KAMLOOPS_FIRE_ZONE_IDS });
    await act(async () => renderAccordion({ store, defaultExpanded: true }));
    fireEvent.click(getAllCheckbox("Kamloops Fire Centre"));
    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual([]);
    });
  });

  it("shows indeterminate state when some fire zone units are selected", () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        subscriptions: [mockFireCentreInfo.fire_zone_units[0].id],
        loading: false,
        error: null,
        fireCentreInfos: [],
        pinnedFireCentre: null,
        subscriptionsInitialized: true,
      },
    });
    renderAccordion({ store, defaultExpanded: true });
    const checkbox = getAllCheckbox("Kamloops Fire Centre");
    expect(checkbox).not.toBeChecked();
    expect(checkbox).toHaveAttribute("data-indeterminate", "true");
    expect(store.getState().settings.subscriptions).toContain(
      mockFireCentreInfo.fire_zone_units[0].id,
    );
    expect(store.getState().settings.subscriptions).not.toContain(
      mockFireCentreInfo.fire_zone_units[1].id,
    );
  });

  it("checkbox is checked when all fire zone units are selected", () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        subscriptions: KAMLOOPS_FIRE_ZONE_IDS,
      },
    });
    renderAccordion({ store, defaultExpanded: true });
    expect(getAllCheckbox("Kamloops Fire Centre")).toBeChecked();
  });

  it("checkbox is unchecked when no fire zone units are selected", async () => {
    await act(() => renderAccordion({ defaultExpanded: true }));
    const checkbox = getAllCheckbox("Kamloops Fire Centre");
    expect(checkbox).not.toBeChecked();
    expect(checkbox).toHaveAttribute("data-indeterminate", "false");
  });

  it("checkbox does not impact fire zone unit ids that are not related to the current fire centre", async () => {
    const initialSubscriptions = [100, 200];
    const store = createConnectedStore({ subscriptions: initialSubscriptions });

    await act(() => renderAccordion({ store, defaultExpanded: true }));

    const allCheckbox = getAllCheckbox("Kamloops Fire Centre");
    fireEvent.click(allCheckbox);

    await waitFor(() => {
      const subs1 = store.getState().settings.subscriptions;
      expect(subs1).toContain(mockFireCentreInfo.fire_zone_units[0].id);
      expect(subs1).toContain(mockFireCentreInfo.fire_zone_units[1].id);
    });
    const subs2 = store.getState().settings.subscriptions;
    expect(subs2).toContain(initialSubscriptions[0]);
    expect(subs2).toContain(initialSubscriptions[1]);

    fireEvent.click(allCheckbox);

    await waitFor(() => {
      const subs3 = store.getState().settings.subscriptions;
      expect(subs3).toContain(initialSubscriptions[0]);
      expect(subs3).toContain(initialSubscriptions[1]);
    });
    const subs4 = store.getState().settings.subscriptions;
    expect(subs4).not.toContain(mockFireCentreInfo.fire_zone_units[0].id);
    expect(subs4).not.toContain(mockFireCentreInfo.fire_zone_units[1].id);
  });

  it("shows error snackbar when subscription update fails", async () => {
    vi.mocked(updateNotificationSettings).mockRejectedValue(
      new Error("server error"),
    );
    vi.spyOn(console, "error").mockImplementation(() => {});

    const store = createConnectedStore();
    await act(async () => renderAccordion({ store, defaultExpanded: true }));

    fireEvent.click(
      screen.getByLabelText("Toggle subscription for K4-Vernon Zone (Vernon)"),
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to update/i)).toBeInTheDocument();
    });
  });

  it("All checkbox on accordion works independently", async () => {
    const store = createConnectedStore({
      fireCentreInfos: mockFireCentreInfos,
      subscriptions: [3, 4],
    });

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfos[0]}
          defaultExpanded={true}
        />
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfos[1]}
          defaultExpanded={true}
        />
      </Provider>,
    );

    const switchPG1 = await screen.findByLabelText(
      "Toggle subscription for G1-Prince George Zone",
    );
    const switchPG2 = await screen.findByLabelText(
      "Toggle subscription for G3-Robson Valley Zone",
    );
    await waitFor(() => {
      expect(switchPG1).toBeChecked();
      expect(switchPG2).toBeChecked();
    });

    const switchK1 = await screen.findByLabelText(
      "Toggle subscription for K2-Kamloops Zone (Kamloops)",
    );
    const switchK2 = await screen.findByLabelText(
      "Toggle subscription for K5-Penticton Zone",
    );
    expect(switchK1).not.toBeChecked();
    expect(switchK2).not.toBeChecked();

    const kamloopsAll = within(getAccordion("Kamloops")).getByLabelText("All");
    fireEvent.click(kamloopsAll);

    await waitFor(() => {
      expect(switchK1).toBeChecked();
      expect(switchK2).toBeChecked();
    });
    await waitFor(() => {
      expect(switchPG1).toBeChecked();
      expect(switchPG2).toBeChecked();
    });

    fireEvent.click(kamloopsAll);

    await waitFor(() => {
      expect(switchK1).not.toBeChecked();
      expect(switchK2).not.toBeChecked();
    });
    await waitFor(() => {
      expect(switchPG1).toBeChecked();
      expect(switchPG2).toBeChecked();
    });
  });
});
