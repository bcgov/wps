import { describe, it, expect, vi, beforeEach } from "vitest";
import { PushNotificationService } from "./pushNotificationService";
import {
  FirebaseMessaging,
  PermissionStatus,
  Importance,
} from "@capacitor-firebase/messaging";
import { Capacitor } from "@capacitor/core";

// Mock the FirebaseMessaging plugin
vi.mock("@capacitor-firebase/messaging", () => ({
  FirebaseMessaging: {
    checkPermissions: vi.fn(),
    requestPermissions: vi.fn(),
    createChannel: vi.fn(),
    getToken: vi.fn(),
    addListener: vi.fn(),
    removeAllListeners: vi.fn(),
  },
  Importance: {
    High: 4,
  },
}));

// Mock Capacitor.getPlatform()
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

describe("PushNotificationService", () => {
  // Reset all mocks before each test
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("initPushNotificationService", () => {
    it("should not call createChannel when platform is iOS", async () => {
      const mockToken = "test-fcm-token";

      // Override Capacitor.getPlatform to return 'ios'
      vi.mocked(Capacitor.getPlatform).mockReturnValue("ios");

      vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
        receive: "granted",
      } as PermissionStatus);

      vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({
        token: mockToken,
      });

      vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({
        remove: vi.fn(),
      });

      const service = new PushNotificationService();
      await service.initPushNotificationService();

      expect(FirebaseMessaging.createChannel).not.toHaveBeenCalled();
    });

    it("should initialize push notifications successfully when permissions are granted", async () => {
      const mockToken = "test-fcm-token";
      const mockOnRegister = vi.fn();

      // Ensure platform is back to Android for this test
      vi.mocked(Capacitor.getPlatform).mockReturnValue("android");

      vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
        receive: "granted",
      } as PermissionStatus);

      vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({
        token: mockToken,
      });

      vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({
        remove: vi.fn(),
      });

      const service = new PushNotificationService({
        onRegister: mockOnRegister,
      });

      // Act
      await service.initPushNotificationService();

      // Assert
      expect(FirebaseMessaging.checkPermissions).toHaveBeenCalledTimes(1);
      expect(FirebaseMessaging.requestPermissions).not.toHaveBeenCalled();
      expect(FirebaseMessaging.createChannel).toHaveBeenCalledTimes(1);
      expect(FirebaseMessaging.getToken).toHaveBeenCalledTimes(1);
      expect(FirebaseMessaging.addListener).toHaveBeenCalledTimes(3);
      expect(mockOnRegister).toHaveBeenCalledWith(mockToken);
    });

    it("should request permissions when not granted initially", async () => {
      const mockToken = "test-fcm-token";

      vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
        receive: "denied",
      } as PermissionStatus);

      vi.mocked(FirebaseMessaging.requestPermissions).mockResolvedValue({
        receive: "granted",
      } as PermissionStatus);

      vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({
        token: mockToken,
      });

      vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({
        remove: vi.fn(),
      });

      const service = new PushNotificationService();

      await service.initPushNotificationService();

      expect(FirebaseMessaging.checkPermissions).toHaveBeenCalledTimes(1);
      expect(FirebaseMessaging.requestPermissions).toHaveBeenCalledTimes(1);
      expect(FirebaseMessaging.createChannel).toHaveBeenCalledTimes(1);
      expect(FirebaseMessaging.getToken).toHaveBeenCalledTimes(1);
    });

    it("should call onError handler when permission request is denied", async () => {
      const mockOnError = vi.fn();

      vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
        receive: "denied",
      } as PermissionStatus);

      vi.mocked(FirebaseMessaging.requestPermissions).mockResolvedValue({
        receive: "denied",
      } as PermissionStatus);

      vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({
        remove: vi.fn(),
      });

      const service = new PushNotificationService({
        onError: mockOnError,
      });

      await service.initPushNotificationService();

      expect(mockOnError).toHaveBeenCalledOnce();
    });

    it("should use custom Android channel when provided", async () => {
      const mockToken = "test-fcm-token";
      const customChannel = {
        id: "custom-channel",
        name: "Custom Channel",
        description: "Custom notifications",
        importance: Importance.High,
        sound: "custom-sound",
      };

      vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
        receive: "granted",
      } as PermissionStatus);

      vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({
        token: mockToken,
      });

      vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({
        remove: vi.fn(),
      });

      const service = new PushNotificationService({
        androidChannel: customChannel,
      });

      await service.initPushNotificationService();

      expect(FirebaseMessaging.createChannel).toHaveBeenCalledWith(
        customChannel,
      );
    });
  });

  describe("unregister", () => {
    it("should unregister all listeners", async () => {
      const mockRemoveAllListeners = vi.fn();
      const mockRemoveListener1 = vi.fn();
      const mockRemoveListener2 = vi.fn();
      const mockRemoveListener3 = vi.fn();

      vi.mocked(FirebaseMessaging.removeAllListeners).mockImplementation(
        mockRemoveAllListeners,
      );

      vi.mocked(FirebaseMessaging.addListener)
        .mockResolvedValueOnce({ remove: mockRemoveListener1 })
        .mockResolvedValueOnce({ remove: mockRemoveListener2 })
        .mockResolvedValueOnce({ remove: mockRemoveListener3 });

      const service = new PushNotificationService();

      // First, initialize to add listeners
      vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
        receive: "granted",
      } as PermissionStatus);

      vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({
        token: "test-token",
      });

      await service.initPushNotificationService();

      await service.unregister();

      expect(FirebaseMessaging.removeAllListeners).toHaveBeenCalledTimes(1);
      expect(mockRemoveListener1).toHaveBeenCalledTimes(1);
      expect(mockRemoveListener2).toHaveBeenCalledTimes(1);
      expect(mockRemoveListener3).toHaveBeenCalledTimes(1);
    });

    it("should handle errors when removing listeners", async () => {
      const mockRemoveListener = vi
        .fn()
        .mockRejectedValue(new Error("Remove failed"));

      vi.mocked(FirebaseMessaging.removeAllListeners).mockRejectedValue(
        new Error("Remove all failed"),
      );

      vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({
        remove: mockRemoveListener,
      });

      const service = new PushNotificationService();

      vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
        receive: "granted",
      } as PermissionStatus);
      vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({
        token: "test-token",
      });
      await service.initPushNotificationService();

      await expect(service.unregister()).resolves.not.toThrow();
    });
  });
});
