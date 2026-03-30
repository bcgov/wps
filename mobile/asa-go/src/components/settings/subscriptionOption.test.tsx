import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import { vi } from "vitest";
import { createTestStore } from "@/testUtils";
import SubscriptionOption from "./SubscriptionOption";
import { FireZoneUnit } from "@/api/fbaAPI";
import {
  getUpdatedSubscriptions,
  setSubscriptions,
} from "@/slices/settingsSlice";

const KAMLOOPS_SWITCH_LABEL =
  "Toggle subscription for K2-Kamloops Zone (Kamloops)";
const VANJAM_LABEL = "G4-VanJam\n(Vanderhoof)";

const getZoneLabel = (label: string) =>
  screen.getByText((_, element) => {
    return element?.tagName === "P" && element.textContent === label;
  });

describe("SubscriptionOption", () => {
  const mockFireZoneUnit: FireZoneUnit = {
    id: 123,
    name: "K2-Kamloops Zone (Kamloops)",
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
        subscriptions: initialSubscriptions,
      },
    });

    const onToggle = (id: number) => {
      const current = store.getState().settings.subscriptions;
      store.dispatch(setSubscriptions(getUpdatedSubscriptions(current, id)));
    };

    return {
      ...render(
        <Provider store={store}>
          <SubscriptionOption
            fireZoneUnit={fireZoneUnit}
            onToggle={onToggle}
            disabled={false}
          />
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

    expect(screen.getByText("K2-Kamloops")).toBeInTheDocument();
  });

  it("renders bracketed location text on a second line", () => {
    renderWithProvider({
      id: 456,
      name: "G4-VanJam Zone (Vanderhoof)",
    });

    expect(getZoneLabel(VANJAM_LABEL)).toBeInTheDocument();
  });

  it("omits redundant bracketed text for the special duplicate labels", () => {
    renderWithProvider({
      id: 789,
      name: "K2-Kamloops Zone (Kamloops)",
    });

    expect(screen.getByText("K2-Kamloops")).toBeInTheDocument();
    expect(screen.queryByText(/\(Kamloops\)/)).not.toBeInTheDocument();
  });

  it("renders with switch unchecked when not subscribed", () => {
    renderWithProvider(mockFireZoneUnit, []);

    const switchEl = screen.getByRole("checkbox", {
      name: KAMLOOPS_SWITCH_LABEL,
    });
    expect(switchEl).not.toBeChecked();
  });

  it("renders with switch checked when subscribed", () => {
    renderWithProvider(mockFireZoneUnit, [123]);

    const switchEl = screen.getByRole("checkbox", {
      name: KAMLOOPS_SWITCH_LABEL,
    });
    expect(switchEl).toBeChecked();
  });

  it("toggles subscription on when clicking the list item (not subscribed)", async () => {
    const { store } = renderWithProvider(mockFireZoneUnit, []);

    const listItemButton = screen.getByRole("button");
    fireEvent.click(listItemButton);

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toContain(123);
    });
  });

  it("toggles subscription off when clicking the list item (already subscribed)", async () => {
    const { store } = renderWithProvider(mockFireZoneUnit, [123]);

    const listItemButton = screen.getByRole("button");
    fireEvent.click(listItemButton);

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).not.toContain(123);
    });
  });

  it("toggles subscription on when toggling the switch (turn on)", async () => {
    const { store } = renderWithProvider(mockFireZoneUnit, []);

    const switchEl = screen.getByRole("checkbox", {
      name: KAMLOOPS_SWITCH_LABEL,
    });
    fireEvent.click(switchEl);

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toContain(123);
    });
  });

  it("toggles subscription off when toggling the switch (turn off)", async () => {
    const { store } = renderWithProvider(mockFireZoneUnit, [123]);

    const switchEl = screen.getByRole("checkbox", {
      name: KAMLOOPS_SWITCH_LABEL,
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
      name: KAMLOOPS_SWITCH_LABEL,
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
