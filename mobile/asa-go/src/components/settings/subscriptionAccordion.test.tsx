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
import { Device } from "@capacitor/device";

vi.mock("@capacitor/device", () => ({
  Device: { getId: vi.fn().mockReturnValue(new Promise(() => {})) },
}));

vi.mock("api/pushNotificationsAPI", () => ({
  getNotificationSettings: vi.fn(),
  updateNotificationSettings: vi.fn(),
  registerToken: vi.fn(),
}));

vi.mock("@/utils/retryWithBackoff", () => ({
  retryWithBackoff: vi.fn((op: () => Promise<unknown>) => op()),
}));

import { getNotificationSettings, updateNotificationSettings } from "api/pushNotificationsAPI";

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

// Mock data
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

describe("SubscriptionAccordion", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(Device.getId).mockResolvedValue({ identifier: "test-device-id" });
    vi.mocked(getNotificationSettings).mockResolvedValue([]);
    vi.mocked(updateNotificationSettings).mockImplementation((_, subs) => Promise.resolve(subs));
  });
  it("renders correctly with fire centre name", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          defaultExpanded={false}
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
        />
      </Provider>,
    );

    const accordionText = screen.getByText(FIRE_CENTRE_LABEL);
    expect(accordionText).toBeInTheDocument();
  });

  it("renders as expanded when defaultExpanded is true", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
          defaultExpanded={true}
        />
      </Provider>,
    );

    expect(getZoneLabel(LILLOOET_ZONE_LABEL)).toBeInTheDocument();
    expect(getZoneLabel(VERNON_ZONE_LABEL)).toBeInTheDocument();
  });

  it("renders as collapsed when defaultExpanded is false", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
          defaultExpanded={false}
        />
      </Provider>,
    );

    expect(getZoneLabel(LILLOOET_ZONE_LABEL)).not.toBeVisible();
    expect(getZoneLabel(VERNON_ZONE_LABEL)).not.toBeVisible();
  });

  it("renders all fire zone units as SubscriptionOptions", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
          defaultExpanded={false}
        />
      </Provider>,
    );

    // Expand the accordion to see the options
    fireEvent.click(getAccordionButton() as HTMLElement);

    expect(getZoneLabel(LILLOOET_ZONE_LABEL)).toBeInTheDocument();
    expect(getZoneLabel(VERNON_ZONE_LABEL)).toBeInTheDocument();
  });

  it("expands and collapses when clicked", async () => {
    const store = createTestStore({
      pushNotification: { pushNotificationPermission: "granted", registeredFcmToken: "test-token", deviceIdError: false },
      networkStatus: { networkStatus: { connected: true, connectionType: "wifi" } },
    });

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
          defaultExpanded={false}
        />
      </Provider>,
    );

    // Initially collapsed - details should not be visible
    expect(getZoneLabel(LILLOOET_ZONE_LABEL)).not.toBeVisible();
    expect(getZoneLabel(VERNON_ZONE_LABEL)).not.toBeVisible();

    // Expand the accordion
    fireEvent.click(getAccordionButton() as HTMLElement);
    expect(getZoneLabel(LILLOOET_ZONE_LABEL)).toBeVisible();
    expect(getZoneLabel(VERNON_ZONE_LABEL)).toBeVisible();

    // Collapse the accordion
    fireEvent.click(getAccordionButton() as HTMLElement);
    await waitFor(() => {
      const lillooetDetails = queryZoneLabel(LILLOOET_ZONE_LABEL);
      const vernonDetails = queryZoneLabel(VERNON_ZONE_LABEL);
      expect(lillooetDetails).not.toBeVisible();
      expect(vernonDetails).not.toBeVisible();
    });
  });

  it("is disabled when disabled prop is true", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={true}
          fireCentreInfo={mockFireCentreInfo}
          defaultExpanded={false}
        />
      </Provider>,
    );

    // Check if the accordion is visually disabled (opacity and grayscale)
    const accordion = getAccordionButton()?.closest(".MuiAccordion-root");
    expect(accordion).toHaveStyle({ opacity: "0.5", filter: "grayscale(1)" });

    // Check if the accordion is not interactive
    fireEvent.click(getAccordionButton() as HTMLElement);
    expect(getZoneLabel(LILLOOET_ZONE_LABEL)).not.toBeVisible();
    expect(getZoneLabel(VERNON_ZONE_LABEL)).not.toBeVisible();
  });

  it("displays filled push pin icon when fire centre is pinned", () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        pinnedFireCentre: mockFireCentreInfo.fire_centre_name,
      },
    });

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
          defaultExpanded={false}
        />
      </Provider>,
    );

    // Check if filled push pin icon is displayed
    expect(getPinButton()).toBeInTheDocument();
    // We can't directly test icon type with RTL, but we can check if the pin icon exists
  });

  it("displays outlined push pin icon when fire centre is not pinned", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
          defaultExpanded={false}
        />
      </Provider>,
    );

    // Check if outlined push pin icon is displayed
    expect(getPinButton()).toBeInTheDocument();
  });

  it("pins the fire centre when pin button is clicked and not already pinned", async () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
          defaultExpanded={false}
        />
      </Provider>,
    );

    // Click the pin button
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

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
          defaultExpanded={false}
        />
      </Provider>,
    );

    // Click the pin button
    fireEvent.click(getPinButton());

    await waitFor(() => {
      expect(store.getState().settings.pinnedFireCentre).toBeNull();
    });
  });

  it("selects all fire zone units when 'All' checkbox is checked", async () => {
    const store = createTestStore({
      settings: { ...settingsReducer(undefined, { type: "unknown" }) },
      pushNotification: { pushNotificationPermission: "granted" as const, registeredFcmToken: "test-token", deviceIdError: false },
      networkStatus: { networkStatus: { connected: true, connectionType: "wifi" } },
    });

    await act(async () =>
      render(
        <Provider store={store}>
          <SubscriptionAccordion
            disabled={false}
            fireCentreInfo={mockFireCentreInfo}
            defaultExpanded={true}
          />
        </Provider>,
      ),
    );

    fireEvent.click(getAllCheckbox("Kamloops Fire Centre"));

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual(
        KAMLOOPS_FIRE_ZONE_IDS,
      );
    });
  });

  it("deselects all fire zone units when 'All' checkbox is unchecked", async () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        subscriptions: KAMLOOPS_FIRE_ZONE_IDS,
      },
      pushNotification: { pushNotificationPermission: "granted" as const, registeredFcmToken: "test-token", deviceIdError: false },
      networkStatus: { networkStatus: { connected: true, connectionType: "wifi" } },
    });

    await act(async () =>
      render(
        <Provider store={store}>
          <SubscriptionAccordion
            disabled={false}
            fireCentreInfo={mockFireCentreInfo}
            defaultExpanded={true}
          />
        </Provider>,
      ),
    );

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
      },
    });

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
          defaultExpanded={true}
        />
      </Provider>,
    );

    // Find the checkbox - when indeterminate, checked should be false
    const checkbox = getAllCheckbox("Kamloops Fire Centre");
    // When indeterminate: checked is false, but subscriptions exist for this fire centre
    expect(checkbox).not.toBeChecked();
    expect(checkbox).toHaveAttribute("data-indeterminate", "true");
    // The checkbox should be in an indeterminate state (not checked but some selected)
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

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
          defaultExpanded={true}
        />
      </Provider>,
    );

    // Find the checkbox and verify it's checked
    const checkbox = getAllCheckbox("Kamloops Fire Centre");
    expect(checkbox).toBeChecked();
  });

  it("checkbox is unchecked when no fire zone units are selected", async () => {
    const store = createTestStore();

    await act(() =>
      render(
        <Provider store={store}>
          <SubscriptionAccordion
            disabled={false}
            fireCentreInfo={mockFireCentreInfo}
            defaultExpanded={true}
            />
        </Provider>,
      ),
    );

    // Find the checkbox and verify it's unchecked
    const checkbox = getAllCheckbox("Kamloops Fire Centre");
    expect(checkbox).not.toBeChecked();
    expect(checkbox).toHaveAttribute("data-indeterminate", "false");
  });

  it("checkbox does not impact fire zone unit ids that are not related to the current fire centre", async () => {
    const initialSubscriptions = [100, 200];

    const store = createTestStore({
      settings: {
        loading: false,
        error: null,
        fireCentreInfos: [],
        pinnedFireCentre: null,
        subscriptions: initialSubscriptions,
        subscriptionsInitialized: false,
      },
      pushNotification: { pushNotificationPermission: "granted" as const, registeredFcmToken: "test-token", deviceIdError: false },
      networkStatus: { networkStatus: { connected: true, connectionType: "wifi" } },
    });

    await act(() =>
      render(
        <Provider store={store}>
          <SubscriptionAccordion
            disabled={false}
            fireCentreInfo={mockFireCentreInfo}
            defaultExpanded={true}
            />
        </Provider>,
      ),
    );

    // Hit toggleAll to add all fire zone unit ids from this fire centre
    const allCheckbox = getAllCheckbox("Kamloops Fire Centre");
    fireEvent.click(allCheckbox);

    // Confirm initial subscriptions are still there and that the current fire centre fire zone units were added
    await waitFor(() => {
      const subs1 = store.getState().settings.subscriptions;
      expect(subs1).toContain(mockFireCentreInfo.fire_zone_units[0].id);
      expect(subs1).toContain(mockFireCentreInfo.fire_zone_units[1].id);
    });
    const subs2 = store.getState().settings.subscriptions;
    expect(subs2).toContain(initialSubscriptions[0]);
    expect(subs2).toContain(initialSubscriptions[1]);

    // Hit toggleAll again to remove fire zone unit ids from this fire centre
    fireEvent.click(allCheckbox);

    // Confirm initial subscriptions are still there and the current fire centre fire zone units are removed
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
    vi.mocked(updateNotificationSettings).mockRejectedValue(new Error("server error"));
    vi.spyOn(console, "error").mockImplementation(() => {});

    const store = createTestStore({
      settings: { ...settingsReducer(undefined, { type: "unknown" }) },
      pushNotification: { pushNotificationPermission: "granted" as const, registeredFcmToken: "test-token", deviceIdError: false },
      networkStatus: { networkStatus: { connected: true, connectionType: "wifi" } },
    });

    await act(async () =>
      render(
        <Provider store={store}>
          <SubscriptionAccordion
            disabled={false}
            fireCentreInfo={mockFireCentreInfo}
            defaultExpanded={true}
          />
        </Provider>,
      ),
    );

    fireEvent.click(screen.getByLabelText("Toggle subscription for K4-Vernon Zone (Vernon)"));

    await waitFor(() => {
      expect(screen.getByText(/Failed to update/i)).toBeInTheDocument();
    });
  });

  it("All checkbox on accordion works independently", async () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        fireCentreInfos: mockFireCentreInfos,
        pinnedFireCentre: null,
        subscriptions: [3, 4],
      },
      pushNotification: { pushNotificationPermission: "granted" as const, registeredFcmToken: "test-token", deviceIdError: false },
      networkStatus: {
        networkStatus: { connected: true, connectionType: "wifi" },
      },
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

    // Confirm that PG fire zones switches are checked as per initial redux state
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

    // Confirm that Kamloops fire centre zone unit switches are unchecked
    const switchK1 = await screen.findByLabelText(
      "Toggle subscription for K2-Kamloops Zone (Kamloops)",
    );
    const switchK2 = await screen.findByLabelText(
      "Toggle subscription for K5-Penticton Zone",
    );
    expect(switchK1).not.toBeChecked();
    expect(switchK2).not.toBeChecked();

    // Find and click the All checkbox for Kamloops fire centre
    const kamloopsAll = within(getAccordion("Kamloops")).getByLabelText("All");
    fireEvent.click(kamloopsAll);

    // expect Kamloops fire centre switches to now be checked
    await waitFor(() => {
      expect(switchK1).toBeChecked();
      expect(switchK2).toBeChecked();
    });

    // expect PG fire centre switches to still be checked
    await waitFor(() => {
      expect(switchPG1).toBeChecked();
      expect(switchPG2).toBeChecked();
    });

    // Click the Kamloops All checkbox again to
    fireEvent.click(kamloopsAll);

    // expect Kamloops fire centre switches to now be unchecked
    await waitFor(() => {
      expect(switchK1).not.toBeChecked();
      expect(switchK2).not.toBeChecked();
    });

    // expect PG fire centre switches to still be checked
    await waitFor(() => {
      expect(switchPG1).toBeChecked();
      expect(switchPG2).toBeChecked();
    });
  });
});
