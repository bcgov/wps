import { describe, it, expect, vi, beforeEach, Mock } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePushNotifications } from "./usePushNotifications";
import { PushNotificationService } from "@/services/pushNotificationService";
import type { PushInitOptions } from "@/services/pushNotificationService";

// Define an interface for the PushNotificationService methods we use
interface IPushNotificationService {
  initPushNotificationService: () => Promise<void>;
  unregister: () => Promise<void>;
}

// Mock the PushNotificationService
vi.mock("@/services/pushNotificationService");

describe("usePushNotifications", () => {
  // Reset all mocks before each test
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should initialize with token null", () => {
    const { result } = renderHook(() => usePushNotifications());
    expect(result.current.token).toBeNull();
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

  it("should set token when onRegister callback is triggered", async () => {
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

    expect(result.current.token).toEqual(testToken);
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
