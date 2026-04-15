import axios from "@/api/axios";
import {
  getNotificationSettings,
  registerToken,
  unregisterToken,
  updateNotificationSettings,
} from "./pushNotificationsAPI";
import { beforeEach, describe, expect, it, Mock, vi } from "vitest";

vi.mock("@/api/axios", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe("pushNotificationsAPI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("registerToken", () => {
    it("posts to device/register with correct payload and returns response", async () => {
      (axios.post as Mock).mockResolvedValue({ data: { success: true } });

      const result = await registerToken(
        "android",
        "my-token",
        "device-1",
        "user-1",
      );

      expect(axios.post).toHaveBeenCalledWith("asa-go/device/register", {
        platform: "android",
        token: "my-token",
        device_id: "device-1",
        user_id: "user-1",
      });
      expect(result).toEqual({ success: true });
    });

    it("passes null user_id when user is not logged in", async () => {
      (axios.post as Mock).mockResolvedValue({ data: { success: true } });

      await registerToken("ios", "my-token", "device-1", null);

      expect(axios.post).toHaveBeenCalledWith(
        "asa-go/device/register",
        expect.objectContaining({ user_id: null }),
      );
    });
  });

  describe("unregisterToken", () => {
    it("posts to device/unregister with token and returns response", async () => {
      (axios.post as Mock).mockResolvedValue({ data: { success: true } });

      const result = await unregisterToken("my-token");

      expect(axios.post).toHaveBeenCalledWith("asa-go/device/unregister", {
        token: "my-token",
      });
      expect(result).toEqual({ success: true });
    });
  });

  describe("getNotificationSettings", () => {
    it("gets device/notification-settings with device_id param and returns source ids", async () => {
      (axios.get as Mock).mockResolvedValue({
        data: { fire_zone_source_ids: ["1", "2", "3"] },
      });

      const result = await getNotificationSettings("device-1");

      expect(axios.get).toHaveBeenCalledWith(
        "asa-go/device/notification-settings",
        {
          params: { device_id: "device-1" },
        },
      );
      expect(result).toEqual(["1", "2", "3"]);
    });

    it("returns empty array when no subscriptions", async () => {
      (axios.get as Mock).mockResolvedValue({
        data: { fire_zone_source_ids: [] },
      });

      const result = await getNotificationSettings("device-1");

      expect(result).toEqual([]);
    });
  });

  describe("updateNotificationSettings", () => {
    it("posts to device/notification-settings with correct payload and returns updated ids", async () => {
      (axios.post as Mock).mockResolvedValue({
        data: { fire_zone_source_ids: ["5", "10"] },
      });

      const result = await updateNotificationSettings("device-1", ["5", "10"]);

      expect(axios.post).toHaveBeenCalledWith(
        "asa-go/device/notification-settings",
        {
          device_id: "device-1",
          fire_zone_source_ids: ["5", "10"],
        },
      );
      expect(result).toEqual(["5", "10"]);
    });

    it("posts empty array to clear all subscriptions", async () => {
      (axios.post as Mock).mockResolvedValue({
        data: { fire_zone_source_ids: [] },
      });

      const result = await updateNotificationSettings("device-1", []);

      expect(axios.post).toHaveBeenCalledWith(
        "asa-go/device/notification-settings",
        {
          device_id: "device-1",
          fire_zone_source_ids: [],
        },
      );
      expect(result).toEqual([]);
    });
  });
});
