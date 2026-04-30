import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useDeviceId } from "./useDeviceId";
import { createTestStore } from "@/testUtils";
import { Provider } from "react-redux";
import React from "react";

vi.mock("@capacitor/device", () => ({
  Device: { getId: vi.fn() },
}));

vi.mock("@capacitor/preferences", () => ({
  Preferences: {
    get: vi.fn().mockResolvedValue({ value: null }),
  },
}));

import { Device } from "@capacitor/device";

function renderWithStore() {
  const store = createTestStore();
  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(Provider, { store, children });
  return { store, ...renderHook(() => useDeviceId(), { wrapper }) };
}

describe("useDeviceId", () => {
  beforeEach(() => {
    vi.mocked(Device.getId).mockResolvedValue({ identifier: "test-device-id" });
  });

  it("returns null before Device.getId resolves", () => {
    vi.mocked(Device.getId).mockReturnValue(new Promise(() => {}));
    const { result } = renderWithStore();
    expect(result.current).toBeNull();
  });

  it("returns the device identifier after resolving", async () => {
    const { result } = renderWithStore();
    await act(async () => {});
    expect(result.current).toBe("test-device-id");
  });

  it("sets deviceIdError in the store when Device.getId fails", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    vi.mocked(Device.getId).mockRejectedValue(new Error("hardware error"));
    const { result, store } = renderWithStore();
    await act(async () => {});
    expect(result.current).toBeNull();
    expect(store.getState().pushNotification.deviceIdError).toBe(true);
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining("Failed to get device ID"),
    );
    consoleSpy.mockRestore();
  });

  it("clears deviceIdError in the store when Device.getId succeeds", async () => {
    const store = createTestStore({
      pushNotification: {
        pushNotificationPermission: "unknown",
        registeredFcmToken: null,
        deviceIdError: true,
        registrationError: false,
        registrationAttempts: 0,
        pendingNotificationData: null,
      },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(Provider, { store, children });
    const { result } = renderHook(() => useDeviceId(), { wrapper });
    await act(async () => {});
    expect(result.current).toBe("test-device-id");
    expect(store.getState().pushNotification.deviceIdError).toBe(false);
  });
});
