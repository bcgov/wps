import { createTestStore } from "@/testUtils";
import { beforeEach, describe, expect, it, Mock, vi } from "vitest";
import pushNotificationReducer, {
  checkPushNotificationPermission,
  initialState,
  PushNotificationState,
  registerDevice,
  setCurrentFcmToken,
  setDeviceIdError,
  setPushNotificationPermission,
  setRegisteredFcmToken,
} from "./pushNotificationSlice";

vi.mock("@capacitor-firebase/messaging", () => ({
  FirebaseMessaging: {
    checkPermissions: vi.fn().mockResolvedValue({ receive: "granted" }),
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

    it("initial state has currentFcmToken null", () => {
      expect(initialState.currentFcmToken).toBeNull();
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

    it("handles setCurrentFcmToken to a value", () => {
      const next = pushNotificationReducer(
        makeState(),
        setCurrentFcmToken("my-current-token"),
      );
      expect(next.currentFcmToken).toBe("my-current-token");
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
  });

  describe("thunks", () => {
    beforeEach(() => {
      vi.resetAllMocks();
    });

    describe("checkPushNotificationPermission", () => {
      it("dispatches granted when Firebase returns granted", async () => {
        const { FirebaseMessaging } =
          await import("@capacitor-firebase/messaging");
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
        const { FirebaseMessaging } =
          await import("@capacitor-firebase/messaging");
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
      it("registers and sets registeredFcmToken when a current token exists", async () => {
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
          pushNotification: {
            ...initialState,
            currentFcmToken: "fcm-token",
          },
        });

        await store.dispatch(registerDevice());

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

      it("is a no-op when there is no current token yet", async () => {
        const { registerToken } = await import("api/pushNotificationsAPI");

        const store = createTestStore();

        await store.dispatch(registerDevice());

        expect(registerToken).not.toHaveBeenCalled();
      });

      it("is a no-op when already registered with the same token", async () => {
        const { registerToken } = await import("api/pushNotificationsAPI");

        const store = createTestStore({
          pushNotification: {
            ...initialState,
            currentFcmToken: "existing-token",
            registeredFcmToken: "existing-token",
          },
        });

        await store.dispatch(registerDevice());

        expect(registerToken).not.toHaveBeenCalled();
      });

      it("re-registers when token has rotated", async () => {
        const { Device } = await import("@capacitor/device");
        const { Capacitor } = await import("@capacitor/core");
        const { registerToken } = await import("api/pushNotificationsAPI");
        (Device.getId as Mock).mockResolvedValue({ identifier: "device-id" });
        (Capacitor.getPlatform as Mock).mockReturnValue("ios");
        (registerToken as Mock).mockResolvedValue(undefined);

        const store = createTestStore({
          pushNotification: {
            ...initialState,
            currentFcmToken: "new-token",
          },
        });

        await store.dispatch(registerDevice());

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

        const store = createTestStore({
          pushNotification: {
            ...initialState,
            currentFcmToken: "fcm-token",
          },
        });

        await store.dispatch(registerDevice());

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
          pushNotification: {
            ...initialState,
            currentFcmToken: "fcm-token",
          },
        });

        await store.dispatch(registerDevice());

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

        const store = createTestStore({
          pushNotification: {
            ...initialState,
            currentFcmToken: "fcm-token",
          },
        });
        await store.dispatch(registerDevice());

        expect(store.getState().pushNotification.registeredFcmToken).toBeNull();
        expect(consoleSpy).toHaveBeenCalled();
        consoleSpy.mockRestore();
      });
    });
  });
});
