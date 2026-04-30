import axios from "api/axios";

export type Platform = "android" | "ios";

interface DeviceRequestResponse {
  success: boolean;
}

export async function registerToken(
  platform: Platform,
  token: string,
  deviceId: string,
  userId: string | null,
): Promise<DeviceRequestResponse> {
  const url = "asa-go/device/register";
  const { data } = await axios.post(url, {
    platform,
    token,
    device_id: deviceId,
    user_id: userId,
  });
  return data;
}

export async function unregisterToken(
  token: string,
): Promise<DeviceRequestResponse> {
  const url = "asa-go/device/unregister";
  const { data } = await axios.post(url, { token });
  return data;
}

export async function getNotificationSettings(
  deviceId: string,
): Promise<string[]> {
  const { data } = await axios.get("asa-go/device/notification-settings", {
    params: { device_id: deviceId },
  });
  return data.fire_zone_source_ids;
}

export async function updateNotificationSettings(
  deviceId: string,
  fireZoneSourceIds: string[],
): Promise<string[]> {
  const { data } = await axios.post("asa-go/device/notification-settings", {
    device_id: deviceId,
    fire_zone_source_ids: fireZoneSourceIds,
  });
  return data.fire_zone_source_ids;
}
