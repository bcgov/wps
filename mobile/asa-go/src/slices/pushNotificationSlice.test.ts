import { createTestStore } from "@/testUtils";
import { beforeEach, describe, expect, it, Mock, vi } from "vitest";
import pushNotificationReducer, {
  checkPushNotificationPermission,
  incrementRegistrationAttempts,
  initialState,
  MAX_REGISTRATION_ATTEMPTS,
  PushNotificationState,
  registerDevice,
  resetRegistrationAttempts,
  setDeviceIdError,
  setPushNotificationPermission,
  setRegisteredFcmToken,
} from "./pushNotificationSlice";

vi.mock("@capacitor-firebase/messaging", () => ({
  FirebaseMessaging: {
    checkPermissions: vi.fn().mockResolvedValue({ receive: "granted" }),
    getToken: vi.fn().mockResolvedValue({ token: "fcm-token" }),
  },
}));

vi.mock("@capacitor/device", () => ({
  Device: { getId: vi.fn().mockResolvedValue({ identifier: "device-id" }) },
}));

vi.mock("@/utils/retryWithBackoff", () => ({
  retryWithBackoff: vi.fn((op: () => Promise<unknown>) => op()),
}));

vi.mock("@capacitor/core", () => ({
  Capacitor: { getPlatform: vi.fn().mockReturnValue("ios") },
}));

vi.mock("api/pushNotificationsAPI", () => ({
  registerToken: vi.fn(),
}));

describe("pushNotificationSlice", () => {
  const makeState = (
    overrides: Partial<PushNotificationState> = {},
  ): PushNotificationState => ({
    ...initialState,
    ...overrides,
  });

  describe("reducers", () => {
    it("returns the initial state", () => {
      expect(pushNotificationReducer(undefined, { type: "unknown" })).toEqual(
        initialState,
      );
    });

    it("initial state has pushNotificationPermission unknown", () => {
      expect(initialState.pushNotificationPermission).toBe("unknown");
    });

    it("initial state has registeredFcmToken null", () => {
      expect(initialState.registeredFcmToken).toBeNull();
    });

    it("initial state has deviceIdError false", () => {
      expect(initialState.deviceIdError).toBe(false);
    });

    it("handles setPushNotificationPermission", () => {
      const next = pushNotificationReducer(
        makeState(),
        setPushNotificationPermission("granted"),
      );
      expect(next.pushNotificationPermission).toBe("granted");
    });

    it("handles setRegisteredFcmToken to a value", () => {
      const next = pushNotificationReducer(
        makeState(),
        setRegisteredFcmToken("my-token"),
      );
      expect(next.registeredFcmToken).toBe("my-token");
    });

    it("handles setRegisteredFcmToken to null", () => {
      const next = pushNotificationReducer(
        makeState({ registeredFcmToken: "my-token" }),
        setRegisteredFcmToken(null),
      );
      expect(next.registeredFcmToken).toBeNull();
    });

    it("handles setDeviceIdError to true", () => {
      const next = pushNotificationReducer(makeState(), setDeviceIdError(true));
      expect(next.deviceIdError).toBe(true);
    });

    it("handles setDeviceIdError to false", () => {
      const next = pushNotificationReducer(
        makeState({ deviceIdError: true }),
        setDeviceIdError(false),
      );
      expect(next.deviceIdError).toBe(false);
    });

    it("handles incrementRegistrationAttempts", () => {
      const next = pushNotificationReducer(makeState(), incrementRegistrationAttempts());
      expect(next.registrationAttempts).toBe(1);
    });

    it("handles resetRegistrationAttempts", () => {
      const next = pushNotificationReducer(
        makeState({ registrationAttempts: 3 }),
        resetRegistrationAttempts(),
      );
      expect(next.registrationAttempts).toBe(0);
    });
  });

  describe("thunks", () => {
    beforeEach(() => {
      vi.resetAllMocks();
    });

    describe("checkPushNotificationPermission", () => {
      it("dispatches granted when Firebase returns granted", async () => {
        const { FirebaseMessaging } = await import(
          "@capacitor-firebase/messaging"
        );
        (FirebaseMessaging.checkPermissions as Mock).mockResolvedValue({
          receive: "granted",
        });

        const store = createTestStore();
        await store.dispatch(checkPushNotificationPermission());

        expect(
          store.getState().pushNotification.pushNotificationPermission,
        ).toBe("granted");
      });

      it("dispatches unknown when Firebase throws", async () => {
        const consoleSpy = vi
          .spyOn(console, "error")
          .mockImplementation(() => {});
        const { FirebaseMessaging } = await import(
          "@capacitor-firebase/messaging"
        );
        (FirebaseMessaging.checkPermissions as Mock).mockRejectedValue(
          new Error("permission error"),
        );

        const store = createTestStore();
        await store.dispatch(checkPushNotificationPermission());

        expect(
          store.getState().pushNotification.pushNotificationPermission,
        ).toBe("unknown");
        consoleSpy.mockRestore();
      });
    });

    describe("registerDevice", () => {
      it("registers and sets registeredFcmToken when not yet registered", async () => {
        const { Device } = await import("@capacitor/device");
        const { Capacitor } = await import("@capacitor/core");
        const { registerToken } = await import("api/pushNotificationsAPI");
        (Device.getId as Mock).mockResolvedValue({ identifier: "device-id" });
        (Capacitor.getPlatform as Mock).mockReturnValue("ios");
        (registerToken as Mock).mockResolvedValue(undefined);

        const store = createTestStore({
          authentication: {
            error: null,
            isAuthenticated: true,
            idir: "test-user",
            authenticating: false,
            tokenRefreshed: false,
            token: undefined,
            idToken: undefined,
          },
        });

        await store.dispatch(registerDevice("fcm-token", null));

        expect(registerToken).toHaveBeenCalledWith(
          "ios",
          "fcm-token",
          "device-id",
          "test-user",
        );
        expect(store.getState().pushNotification.registeredFcmToken).toBe(
          "fcm-token",
        );
      });

      it("is a no-op when already registered with the same token", async () => {
        const { registerToken } = await import("api/pushNotificationsAPI");

        const store = createTestStore();

        await store.dispatch(
          registerDevice("existing-token", "existing-token"),
        );

        expect(registerToken).not.toHaveBeenCalled();
      });

      it("re-registers when token has rotated", async () => {
        const { Device } = await import("@capacitor/device");
        const { Capacitor } = await import("@capacitor/core");
        const { registerToken } = await import("api/pushNotificationsAPI");
        (Device.getId as Mock).mockResolvedValue({ identifier: "device-id" });
        (Capacitor.getPlatform as Mock).mockReturnValue("ios");
        (registerToken as Mock).mockResolvedValue(undefined);

        const store = createTestStore();

        await store.dispatch(registerDevice("new-token", "old-token"));

        expect(registerToken).toHaveBeenCalledWith(
          "ios",
          "new-token",
          "device-id",
          null,
        );
        expect(store.getState().pushNotification.registeredFcmToken).toBe(
          "new-token",
        );
      });

      it("does not set registeredFcmToken when registration fails", async () => {
        const consoleSpy = vi
          .spyOn(console, "error")
          .mockImplementation(() => {});
        const { Device } = await import("@capacitor/device");
        const { Capacitor } = await import("@capacitor/core");
        const { registerToken } = await import("api/pushNotificationsAPI");
        (Device.getId as Mock).mockResolvedValue({ identifier: "device-id" });
        (Capacitor.getPlatform as Mock).mockReturnValue("ios");
        (registerToken as Mock).mockRejectedValue(new Error("backend error"));

        const store = createTestStore();

        await store.dispatch(registerDevice("fcm-token", null));

        expect(store.getState().pushNotification.registeredFcmToken).toBeNull();
        consoleSpy.mockRestore();
      });

      it("uses retryWithBackoff to register and sets token on success", async () => {
        const { Device } = await import("@capacitor/device");
        const { Capacitor } = await import("@capacitor/core");
        const { registerToken } = await import("api/pushNotificationsAPI");
        const { retryWithBackoff } = await import("@/utils/retryWithBackoff");
        (Device.getId as Mock).mockResolvedValue({ identifier: "device-id" });
        (Capacitor.getPlatform as Mock).mockReturnValue("ios");
        (registerToken as Mock).mockResolvedValue(undefined);

        const store = createTestStore({
          authentication: {
            error: null,
            isAuthenticated: true,
            idir: "test-user",
            authenticating: false,
            tokenRefreshed: false,
            token: undefined,
            idToken: undefined,
          },
        });

        await store.dispatch(registerDevice("fcm-token", null));

        expect(retryWithBackoff).toHaveBeenCalledTimes(1);
        expect(store.getState().pushNotification.registeredFcmToken).toBe(
          "fcm-token",
        );
      });

      it("does not set token when retryWithBackoff exhausts retries", async () => {
        const consoleSpy = vi
          .spyOn(console, "error")
          .mockImplementation(() => {});
        const { Device } = await import("@capacitor/device");
        const { Capacitor } = await import("@capacitor/core");
        const { registerToken } = await import("api/pushNotificationsAPI");
        const { retryWithBackoff } = await import("@/utils/retryWithBackoff");
        (Device.getId as Mock).mockResolvedValue({ identifier: "device-id" });
        (Capacitor.getPlatform as Mock).mockReturnValue("ios");
        (registerToken as Mock).mockRejectedValue(
          new Error("persistent error"),
        );
        (retryWithBackoff as Mock).mockRejectedValue(
          new Error("persistent error"),
        );

        const store = createTestStore();
        await store.dispatch(registerDevice("fcm-token", null));

        expect(store.getState().pushNotification.registeredFcmToken).toBeNull();
        expect(consoleSpy).toHaveBeenCalled();
        consoleSpy.mockRestore();
      });

      it("increments registrationAttempts on each failure beyond MAX_REGISTRATION_ATTEMPTS", async () => {
        const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
        const { Device } = await import("@capacitor/device");
        const { Capacitor } = await import("@capacitor/core");
        const { retryWithBackoff } = await import("@/utils/retryWithBackoff");
        (Device.getId as Mock).mockResolvedValue({ identifier: "device-id" });
        (Capacitor.getPlatform as Mock).mockReturnValue("ios");
        (retryWithBackoff as Mock).mockRejectedValue(new Error("persistent error"));

        const store = createTestStore();
        for (let i = 0; i < MAX_REGISTRATION_ATTEMPTS + 1; i++) {
          await store.dispatch(registerDevice("fcm-token", null));
        }

        expect(store.getState().pushNotification.registrationAttempts).toBe(MAX_REGISTRATION_ATTEMPTS + 1);
        expect(store.getState().pushNotification.registrationError).toBe(true);
        consoleSpy.mockRestore();
      });

      it("resets registrationAttempts on successful registration", async () => {
        const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
        const { Device } = await import("@capacitor/device");
        const { Capacitor } = await import("@capacitor/core");
        const { registerToken } = await import("api/pushNotificationsAPI");
        const { retryWithBackoff } = await import("@/utils/retryWithBackoff");
        (Device.getId as Mock).mockResolvedValue({ identifier: "device-id" });
        (Capacitor.getPlatform as Mock).mockReturnValue("ios");

        // Fail up to max, then succeed
        (retryWithBackoff as Mock)
          .mockRejectedValueOnce(new Error("error"))
          .mockRejectedValueOnce(new Error("error"))
          .mockResolvedValueOnce(undefined);
        (registerToken as Mock).mockResolvedValue(undefined);

        const store = createTestStore();
        await store.dispatch(registerDevice("fcm-token", null));
        await store.dispatch(registerDevice("fcm-token", null));
        expect(store.getState().pushNotification.registrationAttempts).toBe(2);

        await store.dispatch(registerDevice("fcm-token", "different-token"));
        expect(store.getState().pushNotification.registrationAttempts).toBe(0);
        consoleSpy.mockRestore();
      });
    });
  });
});
