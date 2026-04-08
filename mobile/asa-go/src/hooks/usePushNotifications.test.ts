import { describe, it, expect, vi, beforeEach, Mock } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePushNotifications } from "./usePushNotifications";
import { PushNotificationService } from "@/services/pushNotificationService";
import type { PushInitOptions } from "@/services/pushNotificationService";
import {
  registerDevice,
  setCurrentFcmToken,
} from "@/slices/pushNotificationSlice";

const dispatchMock = vi.hoisted(() => vi.fn());
const registerDeviceMock = vi.hoisted(() =>
  vi.fn(() => ({
    type: "pushNotification/registerDevice",
  })),
);
const setCurrentFcmTokenMock = vi.hoisted(() =>
  vi.fn((token: string) => ({
    type: "pushNotification/setCurrentFcmToken",
    payload: token,
  })),
);

// Define an interface for the PushNotificationService methods we use
interface IPushNotificationService {
  initPushNotificationService: () => Promise<void>;
  unregister: () => Promise<void>;
}

// Mock the PushNotificationService
vi.mock("@/services/pushNotificationService");
vi.mock("react-redux", () => ({
  useDispatch: () => dispatchMock,
}));
vi.mock("@/slices/pushNotificationSlice", () => ({
  registerDevice: registerDeviceMock,
  setCurrentFcmToken: setCurrentFcmTokenMock,
}));

describe("usePushNotifications", () => {
  // Reset all mocks before each test
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should initialize without a token in hook state", () => {
    const { result } = renderHook(() => usePushNotifications());
    expect(result.current.initPushNotifications).toBeInstanceOf(Function);
  });

  it("should create a PushNotificationService instance and call initPushNotificationService when initPushNotifications is called", async () => {
    // Mock the service methods
    const mockInit = vi.fn().mockResolvedValue(undefined);
    (PushNotificationService as Mock).mockImplementation(function (
      this: IPushNotificationService,
    ) {
      this.initPushNotificationService = mockInit;
      this.unregister = vi.fn();
    });

    const { result } = renderHook(() => usePushNotifications());

    await act(async () => {
      await result.current.initPushNotifications();
    });

    expect(PushNotificationService).toHaveBeenCalledTimes(1);
    expect(mockInit).toHaveBeenCalledTimes(1);
  });

  it("should store the token in Redux and trigger registration when onRegister callback is triggered", async () => {
    const testToken = "test-fcm-token";
    (PushNotificationService as Mock).mockImplementation(function (
      this: IPushNotificationService,
      opts: PushInitOptions,
    ) {
      // Trigger onRegister callback immediately
      opts.onRegister?.(testToken);
      this.initPushNotificationService = vi.fn().mockResolvedValue(undefined);
      this.unregister = vi.fn();
    });

    const { result } = renderHook(() => usePushNotifications());

    await act(async () => {
      await result.current.initPushNotifications();
    });

    expect(setCurrentFcmToken).toHaveBeenCalledWith(testToken);
    expect(registerDevice).toHaveBeenCalledWith();
    expect(dispatchMock).toHaveBeenCalledWith({
      type: "pushNotification/setCurrentFcmToken",
      payload: testToken,
    });
    expect(dispatchMock).toHaveBeenCalledWith({
      type: "pushNotification/registerDevice",
    });
  });

  it("should prevent multiple initializations of PushNotificationService", async () => {
    (PushNotificationService as Mock).mockImplementation(function (
      this: IPushNotificationService,
    ) {
      this.initPushNotificationService = vi.fn().mockResolvedValue(undefined);
      this.unregister = vi.fn();
    });

    const { result } = renderHook(() => usePushNotifications());

    await act(async () => {
      await result.current.initPushNotifications();
      await result.current.initPushNotifications(); // Call again
    });

    expect(PushNotificationService).toHaveBeenCalledTimes(1);
  });

  it("should call unregister on service when component unmounts", async () => {
    const mockUnregister = vi.fn();
    (PushNotificationService as Mock).mockImplementation(function (
      this: IPushNotificationService,
    ) {
      this.initPushNotificationService = vi.fn().mockResolvedValue(undefined);
      this.unregister = mockUnregister;
    });

    const { result, unmount } = renderHook(() => usePushNotifications());

    await act(async () => {
      await result.current.initPushNotifications();
    });

    unmount();

    expect(mockUnregister).toHaveBeenCalledTimes(1);
  });

  it("should pass correct android channel configuration to PushNotificationService", async () => {
    (PushNotificationService as Mock).mockImplementation(function (
      this: IPushNotificationService,
    ) {
      this.initPushNotificationService = vi.fn().mockResolvedValue(undefined);
      this.unregister = vi.fn();
    });

    const { result } = renderHook(() => usePushNotifications());

    await act(async () => {
      await result.current.initPushNotifications();
    });

    expect(PushNotificationService).toHaveBeenCalledWith(
      expect.objectContaining({
        androidChannel: expect.objectContaining({
          id: "general",
          name: "General",
          description: "General notifications",
          importance: 4, // High importance
          sound: "default",
        }),
      }),
    );
  });
});
