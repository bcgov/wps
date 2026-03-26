import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, Mock, vi } from "vitest";
import { useNotificationSettings } from "./useNotificationSettings";
import { createTestStore } from "@/testUtils";
import { Provider } from "react-redux";
import React from "react";

vi.mock("@capacitor/device", () => ({
  Device: {
    getId: vi.fn().mockResolvedValue({ identifier: "test-device-id" }),
  },
}));

vi.mock("api/pushNotificationsAPI", () => ({
  getNotificationSettings: vi.fn(),
  updateNotificationSettings: vi.fn(),
  registerToken: vi.fn(),
}));

vi.mock("@capacitor/preferences", () => ({
  Preferences: {
    get: vi.fn().mockResolvedValue({ value: null }),
    set: vi.fn().mockResolvedValue(undefined),
    remove: vi.fn().mockResolvedValue(undefined),
  },
}));

import { Device } from "@capacitor/device";
import { getNotificationSettings, registerToken, updateNotificationSettings } from "api/pushNotificationsAPI";

const onlineState = {
  networkStatus: { networkStatus: { connected: true, connectionType: "wifi" as "wifi" | "cellular" | "none" | "unknown" } },
  settings: { loading: false, error: null, fireCentreInfos: [], pinnedFireCentre: null, pushNotificationPermission: "granted" as const, subscriptions: [], deviceIdError: false, tokenRegistered: true },
};

const offlineState = {
  networkStatus: { networkStatus: { connected: false, connectionType: "none" as "wifi" | "cellular" | "none" | "unknown" } },
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
    (Device.getId as Mock).mockResolvedValue({ identifier: "test-device-id" });
  });

  it("fetches notification settings on mount when online", async () => {
    (getNotificationSettings as Mock).mockResolvedValue(["1", "2", "3"]);

    const { store } = await act(async () => renderWithStore());

    expect(getNotificationSettings).toHaveBeenCalledWith("test-device-id");
    expect(store.getState().settings.subscriptions).toEqual([1, 2, 3]);
  });

  it("does not fetch when offline", async () => {
    await act(async () => renderWithStore(offlineState));

    expect(getNotificationSettings).not.toHaveBeenCalled();
  });

  it("does not fetch before deviceId is resolved", async () => {
    (Device.getId as Mock).mockReturnValue(new Promise(() => {})); // never resolves

    await act(async () => renderWithStore());

    expect(getNotificationSettings).not.toHaveBeenCalled();
  });

  it("does not fetch when tokenRegistered is false", async () => {
    const store = createTestStore({
      ...onlineState,
      settings: { loading: false, error: null, fireCentreInfos: [], pinnedFireCentre: null, pushNotificationPermission: "granted", subscriptions: [], deviceIdError: false, tokenRegistered: false },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(Provider, { store, children });

    await act(async () => renderHook(() => useNotificationSettings(), { wrapper }));

    expect(getNotificationSettings).not.toHaveBeenCalled();
  });

  it("fetches when tokenRegistered becomes true", async () => {
    (getNotificationSettings as Mock).mockResolvedValue(["1"]);
    const store = createTestStore({
      ...onlineState,
      settings: { loading: false, error: null, fireCentreInfos: [], pinnedFireCentre: null, pushNotificationPermission: "granted", subscriptions: [], deviceIdError: false, tokenRegistered: true },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(Provider, { store, children });

    await act(async () => renderHook(() => useNotificationSettings(), { wrapper }));

    expect(getNotificationSettings).toHaveBeenCalledWith("test-device-id");
  });

  it("updateSubscriptions saves locally and syncs to server when online", async () => {
    (getNotificationSettings as Mock).mockResolvedValue([]);
    (updateNotificationSettings as Mock).mockResolvedValue(["10", "20"]);

    const { result, store } = await act(async () => renderWithStore());

    await act(async () => {
      await result.current.updateSubscriptions([10, 20]);
    });

    expect(updateNotificationSettings).toHaveBeenCalledWith("test-device-id", ["10", "20"]);
    expect(store.getState().settings.subscriptions).toEqual([10, 20]);
  });

  it("updateSubscriptions skips API call when offline", async () => {
    (getNotificationSettings as Mock).mockResolvedValue([]);

    const { result } = await act(async () => renderWithStore(offlineState));

    await act(async () => {
      await result.current.updateSubscriptions([10]);
    });

    expect(updateNotificationSettings).not.toHaveBeenCalled();
  });

  it("rolls back subscription change when offline", async () => {
    const store = createTestStore({
      ...offlineState,
      settings: { loading: false, error: null, fireCentreInfos: [], pinnedFireCentre: null, pushNotificationPermission: "granted", subscriptions: [5], deviceIdError: false, tokenRegistered: true, fcmToken: "tok" },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(Provider, { store, children });

    const { result } = await act(async () => renderHook(() => useNotificationSettings(), { wrapper }));

    await act(async () => {
      await result.current.updateSubscriptions([5, 10]);
    });

    expect(store.getState().settings.subscriptions).toEqual([5]);
  });

  it("rolls back subscription change when deviceId is unavailable", async () => {
    (Device.getId as Mock).mockReturnValue(new Promise(() => {})); // never resolves

    const store = createTestStore({
      ...onlineState,
      settings: { ...onlineState.settings, subscriptions: [5] },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(Provider, { store, children });

    const { result } = await act(async () => renderHook(() => useNotificationSettings(), { wrapper }));

    await act(async () => {
      await result.current.updateSubscriptions([5, 10]);
    });

    expect(store.getState().settings.subscriptions).toEqual([5]);
  });

  it("updateSubscriptions updates state from server response", async () => {
    (getNotificationSettings as Mock).mockResolvedValue([]);
    // server returns different subs than what was sent (e.g. server corrects the list)
    (updateNotificationSettings as Mock).mockResolvedValue(["5", "6"]);

    const { result, store } = await act(async () => renderWithStore());

    await act(async () => {
      await result.current.updateSubscriptions([10, 20]);
    });

    expect(store.getState().settings.subscriptions).toEqual([5, 6]);
  });

  it("toggleSubscription adds a subscription", async () => {
    (getNotificationSettings as Mock).mockResolvedValue(["1"]);
    (updateNotificationSettings as Mock).mockResolvedValue(["1", "2"]);

    const { result, store } = await act(async () => renderWithStore());

    await act(async () => {
      await result.current.toggleSubscription(2);
    });

    expect(updateNotificationSettings).toHaveBeenCalledWith("test-device-id", ["1", "2"]);
    expect(store.getState().settings.subscriptions).toEqual([1, 2]);
  });

  it("toggleSubscription removes an existing subscription", async () => {
    (getNotificationSettings as Mock).mockResolvedValue(["1", "2"]);
    (updateNotificationSettings as Mock).mockResolvedValue(["2"]);

    const { result, store } = await act(async () => renderWithStore());

    await act(async () => {
      await result.current.toggleSubscription(1);
    });

    expect(updateNotificationSettings).toHaveBeenCalledWith("test-device-id", ["2"]);
    expect(store.getState().settings.subscriptions).toEqual([2]);
  });

  it("sets deviceIdError in store when Device.getId fails", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    (Device.getId as Mock).mockRejectedValue(new Error("device unavailable"));

    const { store } = await act(async () => renderWithStore());

    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining("Failed to get device ID"));
    expect(store.getState().settings.deviceIdError).toBe(true);
    consoleSpy.mockRestore();
  });

  it("clears deviceIdError in store when Device.getId succeeds", async () => {
    (getNotificationSettings as Mock).mockResolvedValue([]);
    (Device.getId as Mock).mockResolvedValue({ identifier: "test-device-id" });

    const store = createTestStore({
      settings: { loading: false, error: null, fireCentreInfos: [], pinnedFireCentre: null, pushNotificationPermission: "granted", subscriptions: [], deviceIdError: true },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(Provider, { store, children });

    await act(async () => renderHook(() => useNotificationSettings(), { wrapper }));

    expect(store.getState().settings.deviceIdError).toBe(false);
  });

  it("logs error and keeps local state if fetch fails", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    (getNotificationSettings as Mock).mockRejectedValue(new Error("network error"));

    await act(async () => renderWithStore());

    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining("Failed to fetch"));
    consoleSpy.mockRestore();
  });

  it("retries registration before updating subscriptions when not registered", async () => {
    (getNotificationSettings as Mock).mockResolvedValue([]);
    (registerToken as Mock).mockResolvedValue(undefined);
    (updateNotificationSettings as Mock).mockResolvedValue(["10"]);

    const store = createTestStore({
      ...onlineState,
      settings: { ...onlineState.settings, tokenRegistered: false, fcmToken: "fcm-token" },
      authentication: { loading: false, error: null, isAuthenticated: true, idir: "test-user", email: "test@example.com" },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(Provider, { store, children });
    const { result } = await act(async () => renderHook(() => useNotificationSettings(), { wrapper }));

    await act(async () => {
      await result.current.updateSubscriptions([10]);
    });

    expect(registerToken).toHaveBeenCalledWith(expect.any(String), "fcm-token", "test-device-id", "test-user");
    expect(updateNotificationSettings).toHaveBeenCalled();
    expect(store.getState().settings.tokenRegistered).toBe(true);
  });

  it("rolls back subscription change if retry registration fails", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    (getNotificationSettings as Mock).mockResolvedValue([]);
    (registerToken as Mock).mockRejectedValue(new Error("reg failed"));

    const store = createTestStore({
      ...onlineState,
      settings: { ...onlineState.settings, tokenRegistered: false, fcmToken: "fcm-token", subscriptions: [5] },
      authentication: { loading: false, error: null, isAuthenticated: true, idir: null, email: null },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(Provider, { store, children });
    const { result } = await act(async () => renderHook(() => useNotificationSettings(), { wrapper }));

    await act(async () => {
      await result.current.updateSubscriptions([5, 10]);
    });

    expect(updateNotificationSettings).not.toHaveBeenCalled();
    expect(store.getState().settings.subscriptions).toEqual([5]);
    consoleSpy.mockRestore();
  });

  it("reverts local state when update fails", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    (getNotificationSettings as Mock).mockResolvedValue(["5", "6"]);
    (updateNotificationSettings as Mock).mockRejectedValue(new Error("server error"));

    const { result, store } = await act(async () => renderWithStore());

    await act(async () => {
      await result.current.updateSubscriptions([1]);
    });

    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining("Failed to update"));
    expect(store.getState().settings.subscriptions).toEqual([5, 6]);
    consoleSpy.mockRestore();
  });
});
