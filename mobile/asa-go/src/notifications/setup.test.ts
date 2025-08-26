import { setupPushNotifications } from "@/notifications/setup";
import { PushNotifications } from "@capacitor/push-notifications";
import { vi } from "vitest";

describe("setup push notifications", () => {
  vi.mock("@capacitor/push-notifications", () => ({
    PushNotifications: {
      register: vi.fn(),
      checkPermissions: vi.fn(),
      requestPermissions: vi.fn(),
      addListener: vi.fn(),
    },
  }));

  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(PushNotifications.checkPermissions).mockResolvedValue({
      receive: "granted",
    });
    vi.mocked(PushNotifications.requestPermissions).mockResolvedValue({
      receive: "granted",
    });
    vi.mocked(PushNotifications.register).mockResolvedValue();
    vi.mocked(PushNotifications.addListener).mockResolvedValue({
      remove: vi.fn(),
    });
  });

  it("registers app for push notifications and checks for permissions", async () => {
    await setupPushNotifications();

    expect(PushNotifications.addListener).toHaveBeenCalledTimes(2);
    expect(PushNotifications.addListener).toHaveBeenCalledWith(
      "registration",
      expect.any(Function)
    );
    expect(PushNotifications.addListener).toHaveBeenCalledWith(
      "registrationError",
      expect.any(Function)
    );
    expect(PushNotifications.checkPermissions).toHaveBeenCalled();
    expect(PushNotifications.register).toHaveBeenCalled();
  });

  it("throws error when push notification permissions are denied", async () => {
    vi.mocked(PushNotifications.checkPermissions).mockResolvedValue({
      receive: "denied",
    });

    await expect(setupPushNotifications()).rejects.toThrow(
      "User denied push notification permissions"
    );

    expect(PushNotifications.addListener).toHaveBeenCalledTimes(2);
    expect(PushNotifications.checkPermissions).toHaveBeenCalled();
    expect(PushNotifications.register).not.toHaveBeenCalled();
  });

  it("requests permissions when initially prompted", async () => {
    vi.mocked(PushNotifications.checkPermissions).mockResolvedValue({
      receive: "prompt",
    });
    vi.mocked(PushNotifications.requestPermissions).mockResolvedValue({
      receive: "granted",
    });

    await setupPushNotifications();

    expect(PushNotifications.checkPermissions).toHaveBeenCalled();
    expect(PushNotifications.requestPermissions).toHaveBeenCalled();
    expect(PushNotifications.register).toHaveBeenCalled();
  });
});
