import { describe, expect, it } from "vitest";
import { selectNotificationSetupState, selectNotificationSettingsDisabled } from "@/store";
import type { RootState } from "@/store";

const base = {
  pushNotificationPermission: "granted" as const,
  fcmToken: "some-token",
  tokenRegistered: true,
};

const makeState = (
  overrides: Partial<typeof base>,
  connected = true,
): RootState => ({
  settings: {
    loading: false,
    error: null,
    fireCentreInfos: [],
    pinnedFireCentre: null,
    subscriptions: [],
    deviceIdError: false,
    ...base,
    ...overrides,
  },
  networkStatus: {
    networkStatus: { connected, connectionType: connected ? "wifi" : "none" },
  },
} as unknown as RootState);

describe("selectNotificationSetupState", () => {
  it("returns permissionDenied when permission is denied", () => {
    expect(selectNotificationSetupState(makeState({ pushNotificationPermission: "denied" }))).toBe("permissionDenied");
  });

  it("returns permissionDenied when permission is unknown", () => {
    expect(selectNotificationSetupState(makeState({ pushNotificationPermission: "unknown" as never }))).toBe("permissionDenied");
  });

  it("returns awaitingFCMToken when permission granted but no token", () => {
    expect(selectNotificationSetupState(makeState({ fcmToken: null }))).toBe("awaitingFCMToken");
  });

  it("returns unregistered when token present but not registered", () => {
    expect(selectNotificationSetupState(makeState({ tokenRegistered: false }))).toBe("unregistered");
  });

  it("returns ready when permission granted, token present, and registered", () => {
    expect(selectNotificationSetupState(makeState({}))).toBe("ready");
  });
});

describe("selectNotificationSettingsDisabled", () => {
  it("returns false when ready and online", () => {
    expect(selectNotificationSettingsDisabled(makeState({}))).toBe(false);
  });

  it("returns true when permission denied", () => {
    expect(selectNotificationSettingsDisabled(makeState({ pushNotificationPermission: "denied" }))).toBe(true);
  });

  it("returns true when awaiting FCM token", () => {
    expect(selectNotificationSettingsDisabled(makeState({ fcmToken: null }))).toBe(true);
  });

  it("returns true when unregistered", () => {
    expect(selectNotificationSettingsDisabled(makeState({ tokenRegistered: false }))).toBe(true);
  });

  it("returns true when offline", () => {
    expect(selectNotificationSettingsDisabled(makeState({}, false))).toBe(true);
  });
});
