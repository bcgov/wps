import { describe, expect, it } from "vitest";
import {
  selectNotificationSetupState,
  selectNotificationSettingsDisabled,
} from "@/store";
import type { RootState } from "@/store";

const base: {
  pushNotificationPermission: "granted" | "denied";
  registeredFcmToken: string | null;
  deviceIdError: boolean;
  registrationError: boolean;
} = {
  pushNotificationPermission: "granted" as const,
  registeredFcmToken: "some-token",
  deviceIdError: false,
  registrationError: false,
};

const makeState = (
  overrides: Partial<typeof base>,
  connected = true,
): RootState =>
  ({
    settings: {
      loading: false,
      error: null,
      fireCentreInfos: [],
      pinnedFireCentre: null,
      subscriptions: [],
      subscriptionsInitialized: true,
    },
    pushNotification: {
      ...base,
      ...overrides,
    },
    networkStatus: {
      networkStatus: { connected, connectionType: connected ? "wifi" : "none" },
    },
  } as unknown as RootState);

describe("selectNotificationSetupState", () => {
  it("returns permissionDenied when permission is denied", () => {
    expect(
      selectNotificationSetupState(
        makeState({ pushNotificationPermission: "denied" }),
      ),
    ).toBe("permissionDenied");
  });

  it("returns permissionDenied when permission is unknown", () => {
    expect(
      selectNotificationSetupState(
        makeState({ pushNotificationPermission: "unknown" as never }),
      ),
    ).toBe("permissionDenied");
  });

  it("returns unregistered when registeredFcmToken is null", () => {
    expect(
      selectNotificationSetupState(makeState({ registeredFcmToken: null })),
    ).toBe("unregistered");
  });

  it("returns registrationFailed when token is null and registrationError is true", () => {
    expect(
      selectNotificationSetupState(
        makeState({ registeredFcmToken: null, registrationError: true }),
      ),
    ).toBe("registrationFailed");
  });

  it("returns ready when permission granted and registeredFcmToken is set", () => {
    expect(selectNotificationSetupState(makeState({}))).toBe("ready");
  });
});

describe("selectNotificationSettingsDisabled", () => {
  it("returns false when ready and online", () => {
    expect(selectNotificationSettingsDisabled(makeState({}))).toBe(false);
  });

  it("returns true when permission denied", () => {
    expect(
      selectNotificationSettingsDisabled(
        makeState({ pushNotificationPermission: "denied" }),
      ),
    ).toBe(true);
  });

  it("returns true when unregistered", () => {
    expect(
      selectNotificationSettingsDisabled(
        makeState({ registeredFcmToken: undefined }),
      ),
    ).toBe(true);
  });

  it("returns true when offline", () => {
    expect(selectNotificationSettingsDisabled(makeState({}, false))).toBe(true);
  });

  it("returns true when subscriptions are not yet initialized", () => {
    const state = { ...makeState({}), settings: { ...makeState({}).settings, subscriptionsInitialized: false } };
    expect(selectNotificationSettingsDisabled(state as RootState)).toBe(true);
  });
});

