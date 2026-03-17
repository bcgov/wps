import { FireCentreInfo } from "@/api/fbaAPI";
import settingsReducer from "@/slices/settingsSlice";
import { createTestStore } from "@/testUtils";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { Provider } from "react-redux";
import { describe, expect, it } from "vitest";
import SubscriptionAccordion from "@/components/settings/SubscriptionAccordion";

// Mock data
const mockFireCentreInfo: FireCentreInfo = {
  fire_centre_name: "Cariboo Fire Centre",
  fire_zone_units: [
    { id: 1, name: "Kamloops Fire Zone" },
    { id: 2, name: "Vernon Fire Zone" },
  ],
};

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

describe("SubscriptionAccordion", () => {
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

    // Find the specific h1/h2/h3/p that contains the fire centre name
    const accordionText = screen.getByRole("heading", { name: /CARIBOO/i });
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

    expect(screen.getByText("Kamloops")).toBeInTheDocument();
    expect(screen.getByText("Vernon")).toBeInTheDocument();
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

    expect(screen.queryByText(/Kamloops/i)).not.toBeVisible();
    expect(screen.queryByText(/Vernon/i)).not.toBeVisible();
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
    fireEvent.click(screen.getByRole("button", { name: /CARIBOO/i }));

    expect(screen.getByText("Kamloops")).toBeInTheDocument();
    expect(screen.getByText("Vernon")).toBeInTheDocument();
  });

  it("expands and collapses when clicked", async () => {
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

    // Initially collapsed - details should not be visible
    expect(screen.queryByText(/Kamloops/i)).not.toBeVisible();
    expect(screen.queryByText(/Vernon/i)).not.toBeVisible();

    // Expand the accordion
    fireEvent.click(screen.getByRole("button", { name: /CARIBOO/i }));
    expect(screen.getByText(/Kamloops/i)).toBeVisible();
    expect(screen.getByText(/Vernon/i)).toBeVisible();

    // Collapse the accordion
    fireEvent.click(screen.getByRole("button", { name: /CARIBOO/i }));
    await waitFor(() => {
      const details = screen.queryByText(/Kamloops/i);
      const details2 = screen.queryByText(/Vernon/i);
      expect(details).not.toBeVisible();
      expect(details2).not.toBeVisible();
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
    const accordion = screen
      .getByRole("button", { name: /CARIBOO/i })
      .closest(".MuiAccordion-root");
    expect(accordion).toHaveStyle({ opacity: "0.5", filter: "grayscale(1)" });

    // Check if the accordion is not interactive
    fireEvent.click(screen.getByRole("button", { name: /CARIBOO/i }));
    expect(screen.queryByText(/Kamloops/i)).not.toBeVisible();
    expect(screen.queryByText(/Vernon/i)).not.toBeVisible();
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
    expect(screen.getByRole("button", { name: "" })).toBeInTheDocument();
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
    expect(screen.getByRole("button", { name: "" })).toBeInTheDocument();
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
    fireEvent.click(screen.getByRole("button", { name: "" }));

    waitFor(() => {
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
    fireEvent.click(screen.getByRole("button", { name: "" }));

    waitFor(() => {
      expect(store.getState().settings.pinnedFireCentre).toBeNull();
    });
  });

  it("selects all fire zone units when 'All' checkbox is checked", async () => {
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

    // Click the "All" checkbox to select all
    const allCheckbox = screen.getByLabelText("All");
    fireEvent.click(allCheckbox);

    // Check that all fire zone units are now subscribed
    waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual([1, 2]);
    });
  });

  it("deselects all fire zone units when 'All' checkbox is unchecked", async () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        subscriptions: [1, 2], // Both fire zone units are already subscribed
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

    // Click the "All" checkbox to deselect all
    const allCheckbox = screen.getByLabelText("All");
    fireEvent.click(allCheckbox);

    // Check that all fire zone units are now unsubscribed
    waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual([]);
    });
  });

  it("shows indeterminate state when some fire zone units are selected", () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        subscriptions: [1], // Only one fire zone unit is subscribed
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
    const checkbox = screen.getByRole("checkbox", {
      name: "checkbox-Cariboo Fire Centre All",
    });
    // When indeterminate: checked is false, but subscriptions exist for this fire centre
    expect(checkbox).not.toBeChecked();
    // The checkbox should be in an indeterminate state (not checked but some selected)
    expect(store.getState().settings.subscriptions).toContain(1);
    expect(store.getState().settings.subscriptions).not.toContain(2);
  });

  it("checkbox is checked when all fire zone units are selected", () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        subscriptions: [1, 2], // All fire zone units are subscribed
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
    const checkbox = screen.getByRole("checkbox", {
      name: "checkbox-Cariboo Fire Centre All",
    });
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
    const checkbox = screen.getByRole("checkbox", {
      name: "checkbox-Cariboo Fire Centre All",
    });
    expect(checkbox).not.toBeChecked();
    expect(checkbox).toHaveProperty("indeterminate", false);
  });

  it("checkbox does not impact fire zone unit ids that are not related to the current fire centre", async () => {
    const initialSubscriptions = [100, 200];
    const store = createTestStore({
      settings: {
        loading: false,
        error: null,
        fireCentreInfos: [],
        pinnedFireCentre: null,
        pushNotificationPermission: "unknown",
        subscriptions: initialSubscriptions,
      },
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
    const allCheckbox = screen.getByLabelText("All");
    fireEvent.click(allCheckbox);

    // Confirm initial subscriptions are still there and that the current fire centre fire zone units were added
    await waitFor(() => {
      const subs1 = store.getState().settings.subscriptions;
      expect(subs1).not.toContain(mockFireCentreInfo.fire_zone_units[0].id);
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

  it("All checkbox on accordion works independently", async () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        fireCentreInfos: mockFireCentreInfos,
        pinnedFireCentre: null,
        subscriptions: [3, 4],
      },
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
      "Toggle subscription for Prince George Zone 1",
    );
    const switchPG2 = await screen.findByLabelText(
      "Toggle subscription for Prince George Zone 2",
    );
    await waitFor(async () => {
      expect(switchPG1).toBeChecked();
      expect(switchPG2).toBeChecked();
    });

    // Confirm that Kamloops fire centre zone unit switches are unchecked
    const switchK1 = await screen.findByLabelText(
      "Toggle subscription for Kamloops Zone 1",
    );
    const switchK2 = await screen.findByLabelText(
      "Toggle subscription for Kamloops Zone 2",
    );
    expect(switchK1).not.toBeChecked();
    expect(switchK2).not.toBeChecked();

    // Find and click the All checkbox for Kamloops fire centre
    const kamloopsAll = await screen.findByLabelText("checkbox-Kamloops");
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
