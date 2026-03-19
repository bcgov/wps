import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import { vi } from "vitest";
import { createTestStore } from "@/testUtils";
import { Preferences } from "@capacitor/preferences";
import SubscriptionOption from "./SubscriptionOption";
import { FireZoneUnit } from "@/api/fbaAPI";

vi.mock("@capacitor/preferences", () => ({
  Preferences: {
    get: vi.fn().mockResolvedValue({ value: null }),
    set: vi.fn().mockResolvedValue(undefined),
  },
}));

describe("SubscriptionOption", () => {
  const mockFireZoneUnit: FireZoneUnit = {
    id: 123,
    name: "Kamloops Fire Zone",
  };

  const renderWithProvider = (
    fireZoneUnit: FireZoneUnit,
    initialSubscriptions: number[] = [],
  ) => {
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

    return {
      ...render(
        <Provider store={store}>
          <SubscriptionOption fireZoneUnit={fireZoneUnit} />
        </Provider>,
      ),
      store,
    };
  };

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders the fire zone unit name correctly", () => {
    renderWithProvider(mockFireZoneUnit);

    expect(screen.getByText("Kamloops")).toBeInTheDocument();
  });

  it("renders bracketed location text on a second line", () => {
    renderWithProvider({
      id: 456,
      name: "G4-VanJam Fire Zone (Vanderhoof)",
    });

    expect(screen.getByText("G4-VanJam\n(Vanderhoof)")).toBeInTheDocument();
  });

  it("omits redundant bracketed text for the special duplicate labels", () => {
    renderWithProvider({
      id: 789,
      name: "K2-Kamloops Fire Zone (Kamloops)",
    });

    expect(screen.getByText("K2-Kamloops")).toBeInTheDocument();
    expect(screen.queryByText(/\(Kamloops\)/)).not.toBeInTheDocument();
  });

  it("renders with switch unchecked when not subscribed", () => {
    renderWithProvider(mockFireZoneUnit, []);

    const switchEl = screen.getByRole("checkbox", {
      name: /Toggle subscription for Kamloops Fire Zone/i,
    });
    expect(switchEl).not.toBeChecked();
  });

  it("renders with switch checked when subscribed", () => {
    renderWithProvider(mockFireZoneUnit, [123]);

    const switchEl = screen.getByRole("checkbox", {
      name: /Toggle subscription for Kamloops Fire Zone/i,
    });
    expect(switchEl).toBeChecked();
  });

  it("dispatches saveSubscriptions when clicking the list item (not subscribed)", async () => {
    const { store } = renderWithProvider(mockFireZoneUnit, []);

    const listItemButton = screen.getByRole("button");
    fireEvent.click(listItemButton);

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toContain(123);
    });
    expect(Preferences.set).toHaveBeenCalledWith({
      key: "asaGoSubscriptions",
      value: JSON.stringify([123]),
    });
  });

  it("dispatches saveSubscriptions when clicking the list item (already subscribed)", async () => {
    const { store } = renderWithProvider(mockFireZoneUnit, [123]);

    const listItemButton = screen.getByRole("button");
    fireEvent.click(listItemButton);

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).not.toContain(123);
    });
    expect(Preferences.set).toHaveBeenCalledWith({
      key: "asaGoSubscriptions",
      value: JSON.stringify([]),
    });
  });

  it("dispatches saveSubscriptions when toggling the switch (turn on)", async () => {
    const { store } = renderWithProvider(mockFireZoneUnit, []);

    const switchEl = screen.getByRole("checkbox", {
      name: /Toggle subscription for Kamloops Fire Zone/i,
    });
    fireEvent.click(switchEl);

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toContain(123);
    });
  });

  it("dispatches saveSubscriptions when toggling the switch (turn off)", async () => {
    const { store } = renderWithProvider(mockFireZoneUnit, [123]);

    const switchEl = screen.getByRole("checkbox", {
      name: /Toggle subscription for Kamloops Fire Zone/i,
    });
    fireEvent.click(switchEl);

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).not.toContain(123);
    });
  });

  it("handles multiple subscriptions correctly", async () => {
    const { store } = renderWithProvider(mockFireZoneUnit, [100, 200]);

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual([100, 200]);
    });

    const switchEl = screen.getByRole("checkbox", {
      name: /Toggle subscription for Kamloops Fire Zone/i,
    });
    fireEvent.click(switchEl);

    // All fire zone units should be subscribed to
    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual([100, 200, 123]);
    });

    // Hit toggleAll function again to remove fire zone units associated with this fire centre.
    fireEvent.click(switchEl);

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual([100, 200]);
    });
  });

  it("adds subscription when not in list", async () => {
    const { store } = renderWithProvider(mockFireZoneUnit, [100, 200]);

    const listItemButton = screen.getByRole("button");
    fireEvent.click(listItemButton);

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual([100, 200, 123]);
    });
  });
});
