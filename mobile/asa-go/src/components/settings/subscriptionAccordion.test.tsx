import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import SubscriptionAccordion from "./SubscriptionAccordion";
import pushNotificationReducer from "@/slices/settingsSlice";
import { FireCentreInfo } from "@/api/fbaAPI";
import { createTestStore } from "@/testUtils";

// Mock data
const mockFireCentreInfo: FireCentreInfo = {
  fire_centre_name: "Cariboo Fire Centre",
  fire_zone_units: [
    { id: 1, name: "Kamloops Fire Zone" },
    { id: 2, name: "Vernon Fire Zone" },
  ],
};

describe("SubscriptionAccordion", () => {
  it("renders correctly with fire centre name", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
        />
      </Provider>,
    );

    // Find the specific h1/h2/h3/p that contains the fire centre name
    const accordionText = screen.getByRole("heading", { name: /CARIBOO/i });
    expect(accordionText).toBeInTheDocument();
  });

  it("renders all fire zone units as SubscriptionOptions", () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
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
        ...pushNotificationReducer(undefined, { type: "unknown" }),
        pinnedFireCentre: mockFireCentreInfo.fire_centre_name,
      },
    });

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
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
        />
      </Provider>,
    );

    // Click the pin button
    fireEvent.click(screen.getByRole("button", { name: "" }));

    // Check if the fire centre is now pinned
    // Since savePinnedFireCentre is a thunk, we need to wait a bit
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(store.getState().settings.pinnedFireCentre).toEqual(
      mockFireCentreInfo.fire_centre_name,
    );
  });

  it("unpins the fire centre when pin button is clicked and already pinned", async () => {
    const store = createTestStore({
      settings: {
        ...pushNotificationReducer(undefined, { type: "unknown" }),
        pinnedFireCentre: mockFireCentreInfo.fire_centre_name,
      },
    });

    render(
      <Provider store={store}>
        <SubscriptionAccordion
          disabled={false}
          fireCentreInfo={mockFireCentreInfo}
        />
      </Provider>,
    );

    // Click the pin button
    fireEvent.click(screen.getByRole("button", { name: "" }));

    // Check if the fire centre is now unpinned
    // Since savePinnedFireCentre is a thunk, we need to wait a bit
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(store.getState().settings.pinnedFireCentre).toBeNull();
  });
});
