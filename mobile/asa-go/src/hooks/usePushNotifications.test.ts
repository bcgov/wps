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

describe("usePushNotifications", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(Capacitor.getPlatform).mockReturnValue("android");
  });

  it("initializes with token null", () => {
    const { result } = renderHook(() => usePushNotifications());
    expect(result.current.currentFcmToken).toBeNull();
    expect(result.current.initPushNotifications).toBeInstanceOf(Function);
  });

  it("sets token after successful init", async () => {
    setupFirebaseMocks({ token: "test-fcm-token" });
    const { result } = renderHook(() => usePushNotifications());

    await act(async () => {
      await result.current.initPushNotifications();
    });

    expect(result.current.currentFcmToken).toBe("test-fcm-token");
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

    const { result } = renderHook(() => usePushNotifications());
    await act(async () => {
      await result.current.initPushNotifications();
    });

    await act(async () => {
      tokenListener?.({ token: "refreshed-token" });
    });

    expect(result.current.currentFcmToken).toBe("refreshed-token");
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
    vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
      receive: "denied",
    } as PermissionStatus);
    vi.mocked(FirebaseMessaging.requestPermissions).mockResolvedValue({
      receive: "granted",
    } as PermissionStatus);
    vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({
      token: "test-token",
    });
    vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({
      remove: vi.fn(),
    });

    const { result } = renderHook(() => usePushNotifications());
    await act(async () => {
      await result.current.initPushNotifications();
    });

    expect(FirebaseMessaging.requestPermissions).toHaveBeenCalledTimes(1);
    expect(result.current.currentFcmToken).toBe("test-token");
  });

  it("does not throw when permissions are denied", async () => {
    vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
      receive: "denied",
    } as PermissionStatus);
    vi.mocked(FirebaseMessaging.requestPermissions).mockResolvedValue({
      receive: "denied",
    } as PermissionStatus);
    vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({
      remove: vi.fn(),
    });

    const { result } = renderHook(() => usePushNotifications());
    await expect(
      act(async () => {
        await result.current.initPushNotifications();
      }),
    ).resolves.not.toThrow();
    expect(result.current.currentFcmToken).toBeNull();
  });

  it("does not create Android channel on iOS", async () => {
    vi.mocked(Capacitor.getPlatform).mockReturnValue("ios");
    setupFirebaseMocks();

    const { result } = renderHook(() => usePushNotifications());
    await act(async () => {
      await result.current.initPushNotifications();
    });

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
    await act(async () => {
      await result.current.initPushNotifications();
    });

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

  describe("retryRegistration", () => {
    it("is a no-op when registrationError is false", async () => {
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
          }),
      );

      const { result } = renderHook(() => usePushNotifications());
      await act(async () => {
        await result.current.retryRegistration();
      });

      expect(mockDispatch).not.toHaveBeenCalled();
    });

    it("uses existing token from hook state when available", async () => {
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
          }),
      );
      setupFirebaseMocks({ token: "existing-token" });

      const { result } = renderHook(() => usePushNotifications());
      await act(async () => {
        await result.current.initPushNotifications();
      });

      await act(async () => {
        await result.current.retryRegistration();
      });

      expect(mockDispatch).toHaveBeenCalledWith(setRegistrationError(false));
      expect(mockDispatch).toHaveBeenCalledWith(
        registerDevice("existing-token", null),
      );
      expect(FirebaseMessaging.getToken).toHaveBeenCalledTimes(1); // only from init, not retry
    });

    it("fetches token from Firebase when hook token is null", async () => {
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
          }),
      );
      vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({
        token: "fetched-token",
      });

      const { result } = renderHook(() => usePushNotifications());
      await act(async () => {
        await result.current.retryRegistration();
      });

      expect(mockDispatch).toHaveBeenCalledWith(setRegistrationError(false));
      expect(mockDispatch).toHaveBeenCalledWith(
        registerDevice("fetched-token", null),
      );
      expect(FirebaseMessaging.getToken).toHaveBeenCalledTimes(1);
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
          }),
      );
      vi.mocked(FirebaseMessaging.getToken).mockRejectedValue(
        new Error("token error"),
      );

      const { result } = renderHook(() => usePushNotifications());
      await act(async () => {
        await result.current.retryRegistration();
      });

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
