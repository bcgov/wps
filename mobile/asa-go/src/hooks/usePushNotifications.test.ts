import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePushNotifications } from "./usePushNotifications";
import {
  FirebaseMessaging,
  PermissionStatus,
} from "@capacitor-firebase/messaging";
import { Capacitor } from "@capacitor/core";

vi.mock("@capacitor-firebase/messaging", () => ({
  FirebaseMessaging: {
    checkPermissions: vi.fn(),
    requestPermissions: vi.fn(),
    createChannel: vi.fn(),
    getToken: vi.fn(),
    addListener: vi.fn(),
    removeAllListeners: vi.fn(),
  },
  Importance: { High: 4 },
}));

vi.mock(import("@capacitor/core"), async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    Capacitor: {
      ...actual.Capacitor,
      getPlatform: vi.fn().mockReturnValue("android"),
    },
  };
});

vi.mock("@/hooks/useAppIsActive", () => ({
  useAppIsActive: vi.fn().mockReturnValue(true),
}));

const mockDispatch = vi.fn();
vi.mock("react-redux", () => ({
  useDispatch: () => mockDispatch,
  useSelector: vi.fn((selector: (s: unknown) => unknown) =>
    selector({
      pushNotification: {
        registrationError: false,
        registeredFcmToken: null,
        pushNotificationPermission: "unknown",
        deviceIdError: false,
      },
      networkStatus: {
        networkStatus: { connected: false, connectionType: "none" },
      },
    }),
  ),
}));

vi.mock("@/slices/pushNotificationSlice", async (importOriginal) => {
  const actual = await importOriginal<
    typeof import("@/slices/pushNotificationSlice")
  >();
  return {
    ...actual,
    registerDevice: vi.fn((token: string, registered: string | null) => ({
      type: "registerDevice",
      token,
      registered,
    })),
    setRegistrationError: vi.fn((value: boolean) => ({
      type: "setRegistrationError",
      value,
    })),
  };
});

function setupFirebaseMocks({
  token = "test-fcm-token",
  permissionStatus = "granted",
} = {}) {
  vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
    receive: permissionStatus,
  } as PermissionStatus);
  vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({ token });
  vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({
    remove: vi.fn(),
  });
}

const defaultSelectorState = {
  pushNotification: {
    registrationError: false,
    registeredFcmToken: null,
    pushNotificationPermission: "unknown",
    deviceIdError: false,
  },
  networkStatus: {
    networkStatus: { connected: false, connectionType: "none" },
  },
};

describe("usePushNotifications", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    vi.mocked(Capacitor.getPlatform).mockReturnValue("android");
    const { useSelector } = await import("react-redux");
    vi.mocked(useSelector).mockImplementation(
      (selector: (s: unknown) => unknown) => selector(defaultSelectorState),
    );
  });

  it("initializes and exposes initPushNotifications and retryRegistration", () => {
    const { result } = renderHook(() => usePushNotifications());
    expect(result.current.initPushNotifications).toBeInstanceOf(Function);
    expect(result.current.retryRegistration).toBeInstanceOf(Function);
  });

  it("sets token after successful init", async () => {
    setupFirebaseMocks({ token: "test-fcm-token" });
    const { result } = renderHook(() => usePushNotifications());

    await act(async () => {
      await result.current.initPushNotifications();
    });

    expect(FirebaseMessaging.getToken).toHaveBeenCalledTimes(1);
  });

  it("updates token when tokenReceived fires", async () => {
    let tokenListener: ((e: { token: string }) => void) | undefined;
    setupFirebaseMocks({ token: "initial-token" });
    vi.mocked(FirebaseMessaging.addListener).mockImplementation(
      async (event, handler) => {
        if ((event as string) === "tokenReceived")
          tokenListener = handler as unknown as typeof tokenListener;
        return { remove: vi.fn() };
      },
    );
    const { registerDevice } = await import("@/slices/pushNotificationSlice");
    const { useSelector } = await import("react-redux");
    vi.mocked(useSelector).mockImplementation(
      (selector: (s: unknown) => unknown) =>
        selector({
          pushNotification: {
            registrationError: false,
            registeredFcmToken: null,
            pushNotificationPermission: "unknown",
            deviceIdError: false,
          },
          networkStatus: {
            networkStatus: { connected: true, connectionType: "wifi" },
          },
        }),
    );

    const { result } = renderHook(() => usePushNotifications());
    await act(async () => { await result.current.initPushNotifications(); });

    await act(async () => { tokenListener?.({ token: "refreshed-token" }); });

    expect(mockDispatch).toHaveBeenCalledWith(registerDevice("refreshed-token", null));
  });

  it("prevents multiple initializations", async () => {
    setupFirebaseMocks();
    const { result } = renderHook(() => usePushNotifications());

    await act(async () => {
      await result.current.initPushNotifications();
      await result.current.initPushNotifications();
    });

    expect(FirebaseMessaging.getToken).toHaveBeenCalledTimes(1);
  });

  it("requests permissions when not initially granted", async () => {
    vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({ receive: "denied" } as PermissionStatus);
    vi.mocked(FirebaseMessaging.requestPermissions).mockResolvedValue({ receive: "granted" } as PermissionStatus);
    vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({ token: "test-token" });
    vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({ remove: vi.fn() });

    const { result } = renderHook(() => usePushNotifications());
    await act(async () => { await result.current.initPushNotifications(); });

    expect(FirebaseMessaging.requestPermissions).toHaveBeenCalledTimes(1);
  });

  it("does not throw when permissions are denied", async () => {
    vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({ receive: "denied" } as PermissionStatus);
    vi.mocked(FirebaseMessaging.requestPermissions).mockResolvedValue({ receive: "denied" } as PermissionStatus);
    vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({ remove: vi.fn() });

    const { result } = renderHook(() => usePushNotifications());
    await expect(act(async () => { await result.current.initPushNotifications(); })).resolves.not.toThrow();
  });

  it("does not create Android channel on iOS", async () => {
    vi.mocked(Capacitor.getPlatform).mockReturnValue("ios");
    setupFirebaseMocks();

    const { result } = renderHook(() => usePushNotifications());
    await act(async () => { await result.current.initPushNotifications(); });

    expect(FirebaseMessaging.createChannel).not.toHaveBeenCalled();
  });

  it("removes all listeners on unmount only when initialized", async () => {
    const remove1 = vi.fn();
    const remove2 = vi.fn();
    const remove3 = vi.fn();
    vi.mocked(FirebaseMessaging.addListener)
      .mockResolvedValueOnce({ remove: remove1 })
      .mockResolvedValueOnce({ remove: remove2 })
      .mockResolvedValueOnce({ remove: remove3 });
    setupFirebaseMocks();

    const { result, unmount } = renderHook(() => usePushNotifications());
    await act(async () => { await result.current.initPushNotifications(); });

    unmount();

    expect(FirebaseMessaging.removeAllListeners).toHaveBeenCalledTimes(1);
    expect(remove1).toHaveBeenCalledTimes(1);
    expect(remove2).toHaveBeenCalledTimes(1);
    expect(remove3).toHaveBeenCalledTimes(1);
  });

  it("does not call removeAllListeners on unmount when not initialized", () => {
    const { unmount } = renderHook(() => usePushNotifications());
    unmount();
    expect(FirebaseMessaging.removeAllListeners).not.toHaveBeenCalled();
  });

  describe("registerDevice effect", () => {
    it("dispatches registerDevice when connected and token is available", async () => {
      const { registerDevice } = await import("@/slices/pushNotificationSlice");
      const { useSelector } = await import("react-redux");
      vi.mocked(useSelector).mockImplementation(
        (selector: (s: unknown) => unknown) =>
          selector({
            pushNotification: {
              registrationError: false,
              registeredFcmToken: null,
              pushNotificationPermission: "unknown",
              deviceIdError: false,
            },
            networkStatus: {
              networkStatus: { connected: true, connectionType: "wifi" },
            },
          }),
      );
      setupFirebaseMocks({ token: "test-fcm-token" });

      const { result } = renderHook(() => usePushNotifications());
      await act(async () => { await result.current.initPushNotifications(); });

      expect(mockDispatch).toHaveBeenCalledWith(registerDevice("test-fcm-token", null));
    });

    it("does not dispatch registerDevice when offline", async () => {
      const { registerDevice } = await import("@/slices/pushNotificationSlice");
      setupFirebaseMocks({ token: "test-fcm-token" });

      const { result } = renderHook(() => usePushNotifications());
      await act(async () => { await result.current.initPushNotifications(); });

      expect(mockDispatch).not.toHaveBeenCalledWith(
        registerDevice("test-fcm-token", null),
      );
    });
  });

  describe("retryRegistration", () => {
    it("is a no-op when registrationError is false", async () => {
      const { result } = renderHook(() => usePushNotifications());
      await act(async () => { await result.current.retryRegistration(); });

      expect(mockDispatch).not.toHaveBeenCalled();
    });

    it("fetches token and dispatches registerDevice", async () => {
      const { useSelector } = await import("react-redux");
      const { setRegistrationError, registerDevice } = await import(
        "@/slices/pushNotificationSlice"
      );
      vi.mocked(useSelector).mockImplementation(
        (selector: (s: unknown) => unknown) =>
          selector({
            pushNotification: {
              registrationError: true,
              registeredFcmToken: null,
              pushNotificationPermission: "unknown",
              deviceIdError: false,
            },
            networkStatus: {
              networkStatus: { connected: false, connectionType: "none" },
            },
          }),
      );
      vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({ token: "retry-token" });

      const { result } = renderHook(() => usePushNotifications());
      await act(async () => { await result.current.retryRegistration(); });

      expect(mockDispatch).toHaveBeenCalledWith(setRegistrationError(false));
      expect(mockDispatch).toHaveBeenCalledWith(registerDevice("retry-token", null));
    });

    it("restores registrationError and does not dispatch registerDevice when getToken fails", async () => {
      const consoleSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});
      const { useSelector } = await import("react-redux");
      const { setRegistrationError, registerDevice } = await import(
        "@/slices/pushNotificationSlice"
      );
      vi.mocked(useSelector).mockImplementation(
        (selector: (s: unknown) => unknown) =>
          selector({
            pushNotification: {
              registrationError: true,
              registeredFcmToken: null,
              pushNotificationPermission: "unknown",
              deviceIdError: false,
            },
            networkStatus: {
              networkStatus: { connected: false, connectionType: "none" },
            },
          }),
      );
      vi.mocked(FirebaseMessaging.getToken).mockRejectedValue(
        new Error("token error"),
      );

      const { result } = renderHook(() => usePushNotifications());
      await act(async () => { await result.current.retryRegistration(); });

      expect(mockDispatch).toHaveBeenNthCalledWith(1, setRegistrationError(false));
      expect(mockDispatch).toHaveBeenNthCalledWith(2, setRegistrationError(true));
      expect(mockDispatch).not.toHaveBeenCalledWith(
        registerDevice(expect.anything(), null),
      );
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });
});
