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
  const url = "device/register";
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
  const url = "device/unregister";
  const { data } = await axios.post(url, { token });
  return data;
}
