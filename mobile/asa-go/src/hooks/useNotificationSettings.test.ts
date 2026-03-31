import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, Mock, vi } from "vitest";
import { useNotificationSettings } from "./useNotificationSettings";
import { createTestStore } from "@/testUtils";
import { Provider } from "react-redux";
import React from "react";

vi.mock("api/pushNotificationsAPI", () => ({
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

import { updateNotificationSettings } from "api/pushNotificationsAPI";
import { retryWithBackoff } from "@/utils/retryWithBackoff";

const onlineState = {
  networkStatus: {
    networkStatus: {
      connected: true,
      connectionType: "wifi" as "wifi" | "cellular" | "none" | "unknown",
    },
  },
  settings: {
    loading: false,
    error: null,
    fireCentreInfos: [],
    pinnedFireCentre: null,
    subscriptions: [] as number[],
    subscriptionsInitialized: false,
  },
  pushNotification: {
    pushNotificationPermission: "granted" as const,
    registeredFcmToken: "test-token",
    deviceIdError: false,
  },
};

const offlineState = {
  networkStatus: {
    networkStatus: {
      connected: false,
      connectionType: "none" as "wifi" | "cellular" | "none" | "unknown",
    },
  },
};

function renderWithStore(storeState = onlineState) {
  const store = createTestStore(storeState);
  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(Provider, { store, children });
  return { store, ...renderHook(() => useNotificationSettings(), { wrapper }) };
}

describe("useNotificationSettings", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses retryWithBackoff when updating subscriptions", async () => {
    (updateNotificationSettings as Mock).mockResolvedValue(["1"]);

    const { result } = await act(async () => renderWithStore());
    vi.clearAllMocks();

    await act(async () => {
      await result.current.updateSubscriptions([1]);
    });

    expect(retryWithBackoff).toHaveBeenCalledTimes(1);
  });

  it("updateSubscriptions saves locally and syncs to server when online", async () => {
    (updateNotificationSettings as Mock).mockResolvedValue(["10", "20"]);

    const { result, store } = await act(async () => renderWithStore());

    await act(async () => {
      await result.current.updateSubscriptions([10, 20]);
    });

    expect(updateNotificationSettings).toHaveBeenCalledWith("test-device-id", [
      "10",
      "20",
    ]);
    expect(store.getState().settings.subscriptions).toEqual([10, 20]);
  });

  it("updateSubscriptions skips API call when offline", async () => {
    const { result } = await act(async () =>
      renderWithStore({ ...onlineState, ...offlineState }),
    );

    await act(async () => {
      await result.current.updateSubscriptions([10]);
    });

    expect(updateNotificationSettings).not.toHaveBeenCalled();
  });

  it("rolls back subscription change when offline", async () => {
    const store = createTestStore({
      ...offlineState,
      settings: {
        loading: false,
        error: null,
        fireCentreInfos: [],
        pinnedFireCentre: null,
        subscriptions: [5],
        subscriptionsInitialized: false,
      },
      pushNotification: {
        pushNotificationPermission: "granted" as const,
        registeredFcmToken: "tok",
        deviceIdError: false,
      },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(Provider, { store, children });

    const { result } = await act(async () =>
      renderHook(() => useNotificationSettings(), { wrapper }),
    );

    await act(async () => {
      await result.current.updateSubscriptions([5, 10]);
    });

    expect(store.getState().settings.subscriptions).toEqual([5]);
  });

  it("updateSubscriptions updates state from server response", async () => {
    // server returns different subs than what was sent (e.g. server corrects the list)
    (updateNotificationSettings as Mock).mockResolvedValue(["5", "6"]);

    const { result, store } = await act(async () => renderWithStore());

    await act(async () => {
      await result.current.updateSubscriptions([10, 20]);
    });

    expect(store.getState().settings.subscriptions).toEqual([5, 6]);
  });

  it("toggleSubscription adds a subscription", async () => {
    (updateNotificationSettings as Mock).mockResolvedValue(["1", "2"]);

    const { result, store } = await act(async () =>
      renderWithStore({ ...onlineState, settings: { ...onlineState.settings, subscriptions: [1] } }),
    );

    await act(async () => {
      await result.current.toggleSubscription(2);
    });

    expect(updateNotificationSettings).toHaveBeenCalledWith("test-device-id", [
      "1",
      "2",
    ]);
    expect(store.getState().settings.subscriptions).toEqual([1, 2]);
  });

  it("toggleSubscription removes an existing subscription", async () => {
    (updateNotificationSettings as Mock).mockResolvedValue(["2"]);

    const { result, store } = await act(async () =>
      renderWithStore({ ...onlineState, settings: { ...onlineState.settings, subscriptions: [1, 2] } }),
    );

    await act(async () => {
      await result.current.toggleSubscription(1);
    });

    expect(updateNotificationSettings).toHaveBeenCalledWith("test-device-id", [
      "2",
    ]);
    expect(store.getState().settings.subscriptions).toEqual([2]);
  });

  it("rolls back subscription change when not registered", async () => {
    const store = createTestStore({
      ...onlineState,
      settings: { ...onlineState.settings, subscriptions: [5] },
      pushNotification: {
        pushNotificationPermission: "granted" as const,
        registeredFcmToken: null,
        deviceIdError: false,
      },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(Provider, { store, children });
    const { result } = await act(async () =>
      renderHook(() => useNotificationSettings(), { wrapper }),
    );

    await act(async () => {
      await result.current.updateSubscriptions([5, 10]);
    });

    expect(updateNotificationSettings).not.toHaveBeenCalled();
    expect(store.getState().settings.subscriptions).toEqual([5]);
  });

  it("reverts local state when update fails", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    (updateNotificationSettings as Mock).mockRejectedValue(
      new Error("server error"),
    );

    const { result, store } = await act(async () =>
      renderWithStore({ ...onlineState, settings: { ...onlineState.settings, subscriptions: [5, 6] } }),
    );

    await act(async () => {
      await result.current.updateSubscriptions([1]).catch(() => {});
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining("Failed to update"),
    );
    expect(store.getState().settings.subscriptions).toEqual([5, 6]);
    consoleSpy.mockRestore();
  });

  it("sets updateError to true when update fails", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    (updateNotificationSettings as Mock).mockRejectedValue(
      new Error("server error"),
    );

    const { result } = await act(async () => renderWithStore());

    await act(async () => {
      await result.current.updateSubscriptions([1]).catch(() => {});
    });

    expect(result.current.updateError).toBe(true);
    consoleSpy.mockRestore();
  });

  it("clears updateError after a successful update", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    (updateNotificationSettings as Mock)
      .mockRejectedValueOnce(new Error("server error"))
      .mockResolvedValueOnce(["1"]);

    const { result } = await act(async () => renderWithStore());

    await act(async () => {
      await result.current.updateSubscriptions([1]).catch(() => {});
    });
    expect(result.current.updateError).toBe(true);

    await act(async () => {
      await result.current.updateSubscriptions([1]);
    });
    expect(result.current.updateError).toBe(false);
    consoleSpy.mockRestore();
  });
});
