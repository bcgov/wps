import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, Mock, vi } from "vitest";
import { useInitSubscriptions } from "./useInitSubscriptions";
import { createTestStore } from "@/testUtils";
import { Provider } from "react-redux";
import React from "react";

vi.mock("api/pushNotificationsAPI", () => ({
  getNotificationSettings: vi.fn(),
  updateNotificationSettings: vi.fn(),
}));

vi.mock("@/utils/retryWithBackoff", () => ({
  retryWithBackoff: vi.fn((op: () => Promise<unknown>) => op()),
}));

vi.mock("@capacitor/device", () => ({
  Device: {
    getId: vi.fn().mockResolvedValue({ identifier: "test-device-id" }),
  },
}));

vi.mock("@capacitor/preferences", () => ({
  Preferences: {
    get: vi.fn().mockResolvedValue({ value: null }),
    set: vi.fn().mockResolvedValue(undefined),
    remove: vi.fn().mockResolvedValue(undefined),
  },
}));

import { getNotificationSettings } from "api/pushNotificationsAPI";
import { retryWithBackoff } from "@/utils/retryWithBackoff";
import { setSubscriptions } from "@/slices/settingsSlice";

const onlineState = {
  networkStatus: {
    networkStatus: {
      connected: true,
      connectionType: "wifi" as "wifi" | "cellular" | "none" | "unknown",
    },
  },
  pushNotification: {
    pushNotificationPermission: "granted" as const,
    registeredFcmToken: "test-token" as string | null,
    deviceIdError: false,
  },
};

function renderWithStore(storeState = onlineState) {
  const store = createTestStore(storeState);
  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(Provider, { store, children });
  return { store, ...renderHook(() => useInitSubscriptions(), { wrapper }) };
}

describe("useInitSubscriptions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches notification settings on mount when online", async () => {
    (getNotificationSettings as Mock).mockResolvedValue(["1", "2", "3"]);

    const { store } = await act(async () => renderWithStore());

    expect(getNotificationSettings).toHaveBeenCalledWith("test-device-id");
    expect(store.getState().settings.subscriptions).toEqual([1, 2, 3]);
  });

  it("does not fetch when offline", async () => {
    await act(async () =>
      renderWithStore({
        ...onlineState,
        networkStatus: {
          networkStatus: { connected: false, connectionType: "none" as const },
        },
      }),
    );

    expect(getNotificationSettings).not.toHaveBeenCalled();
  });

  it("does not fetch when not registered", async () => {
    await act(async () =>
      renderWithStore({
        ...onlineState,
        pushNotification: {
          pushNotificationPermission: "granted" as const,
          registeredFcmToken: null,
          deviceIdError: false,
        },
      }),
    );

    expect(getNotificationSettings).not.toHaveBeenCalled();
  });

  it("uses retryWithBackoff when fetching", async () => {
    (getNotificationSettings as Mock).mockResolvedValue(["1"]);

    await act(async () => renderWithStore());

    expect(retryWithBackoff).toHaveBeenCalledTimes(1);
  });

  it("does not fetch when subscriptions are already initialized", async () => {
    const store = createTestStore({
      ...onlineState,
      settings: {
        loading: false,
        error: null,
        fireCentreInfos: [],
        pinnedFireCentre: null,
        subscriptions: [5],
        subscriptionsInitialized: true,
      },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(Provider, { store, children });

    await act(async () => renderHook(() => useInitSubscriptions(), { wrapper }));

    expect(getNotificationSettings).not.toHaveBeenCalled();
    expect(store.getState().settings.subscriptions).toEqual([5]);
  });

  it("does not overwrite subscriptions if a user action occurred while fetch was in-flight", async () => {
    let resolveFetch!: (ids: string[]) => void;
    (getNotificationSettings as Mock).mockReturnValue(
      new Promise<string[]>((resolve) => {
        resolveFetch = resolve;
      }),
    );

    const { store } = renderWithStore();

    // Simulate user action while fetch is in-flight
    act(() => {
      store.dispatch(setSubscriptions([10]));
    });

    // Resolve the fetch with different data
    await act(async () => {
      resolveFetch(["5", "6"]);
    });

    // Fetch result should be discarded — user action wins
    expect(store.getState().settings.subscriptions).toEqual([10]);
  });

  it("logs error and keeps local state if fetch fails", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    (getNotificationSettings as Mock).mockRejectedValue(
      new Error("network error"),
    );

    await act(async () => renderWithStore());

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining("Failed to fetch"),
    );
    consoleSpy.mockRestore();
  });
});
