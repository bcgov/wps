import { describe, expect, it } from "vitest";
import {
  selectNotificationSetupState,
  selectNotificationSettingsDisabled,
  selectNotificationSettingsDisabledReason,
} from "@/store";
import type { RootState } from "@/store";

const base: {
  pushNotificationPermission: "granted" | "denied";
  registeredFcmToken: string | null;
  deviceIdError: boolean;
} = {
  pushNotificationPermission: "granted" as const,
  registeredFcmToken: "some-token",
  deviceIdError: false,
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
});

describe("selectNotificationSettingsDisabledReason", () => {
  it("returns undefined when ready and online", () => {
    expect(
      selectNotificationSettingsDisabledReason(makeState({})),
    ).toBeUndefined();
  });

  it("returns offline message when not connected", () => {
    expect(selectNotificationSettingsDisabledReason(makeState({}, false))).toBe(
      "Unavailable offline",
    );
  });

  it("returns device ID error message when deviceIdError is true", () => {
    expect(
      selectNotificationSettingsDisabledReason(
        makeState({ registeredFcmToken: undefined, deviceIdError: true }),
      ),
    ).toBe("Unable to identify device");
  });

  it("returns permission message when permission denied", () => {
    expect(
      selectNotificationSettingsDisabledReason(
        makeState({ pushNotificationPermission: "denied" }),
      ),
    ).toBe("Enable notifications in device settings");
  });

  it("prioritises offline over permission denied", () => {
    expect(
      selectNotificationSettingsDisabledReason(
        makeState({ pushNotificationPermission: "denied" }, false),
      ),
    ).toBe("Unavailable offline");
  });

  it("prioritises device ID error over permission denied", () => {
    expect(
      selectNotificationSettingsDisabledReason(
        makeState({
          pushNotificationPermission: "denied",
          deviceIdError: true,
        }),
      ),
    ).toBe("Unable to identify device");
  });
});
