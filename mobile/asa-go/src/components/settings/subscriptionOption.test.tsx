import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import SubscriptionOption from "./SubscriptionOption";
import settingsReducer from "@/slices/settingsSlice";
import { createTestStore } from "@/testUtils";
import { FireZoneUnit } from "@/api/fbaAPI";

// Mock data
const mockFireZoneUnit: FireZoneUnit = {
  id: 1,
  name: "Kamloops Fire Zone",
};

describe("SubscriptionOption", () => {
  it("renders correctly with fire zone unit name", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <SubscriptionOption fireZoneUnit={mockFireZoneUnit} />
      </Provider>,
    );

    expect(screen.getByText("Kamloops")).toBeInTheDocument();
  });

  it("displays switch as unchecked when fire zone unit is not subscribed", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <SubscriptionOption fireZoneUnit={mockFireZoneUnit} />
      </Provider>,
    );

    const switchElement = screen.getByRole("checkbox");
    expect(switchElement).not.toBeChecked();
  });

  it("displays switch as checked when fire zone unit is subscribed", () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        subscriptions: [mockFireZoneUnit.id],
      },
    });

    render(
      <Provider store={store}>
        <SubscriptionOption fireZoneUnit={mockFireZoneUnit} />
      </Provider>,
    );

    const switchElement = screen.getByRole("checkbox");
    expect(switchElement).toBeChecked();
  });

  it("subscribes to fire zone unit when switch is toggled on", async () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <SubscriptionOption fireZoneUnit={mockFireZoneUnit} />
      </Provider>,
    );

    const switchElement = screen.getByRole("checkbox");
    fireEvent.click(switchElement);

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual([
        mockFireZoneUnit.id,
      ]);
    });
  });

  it("unsubscribes from fire zone unit when switch is toggled off", async () => {
    const store = createTestStore({
      settings: {
        ...settingsReducer(undefined, { type: "unknown" }),
        subscriptions: [mockFireZoneUnit.id],
      },
    });

    render(
      <Provider store={store}>
        <SubscriptionOption fireZoneUnit={mockFireZoneUnit} />
      </Provider>,
    );

    const switchElement = screen.getByRole("checkbox");
    fireEvent.click(switchElement);

    await waitFor(() => {
      expect(store.getState().settings.subscriptions).toEqual([]);
    });
  });

  it("formats fire zone unit name correctly using nameFormatter", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <SubscriptionOption fireZoneUnit={mockFireZoneUnit} />
      </Provider>,
    );

    expect(screen.getByText("Kamloops")).toBeInTheDocument();
  });
});
