import axios from "api/axios";

export type Platform = "android" | "ios";

export interface RegisterDeviceRequest {
  platform: Platform;
  token: string;
  deviceId: string;
  userId: string | null;
}

export interface UnregisterDeviceRequest {
  token: string;
}

interface DeviceRequestResponse {
  success: boolean;
}

export async function registerToken(
  platform: Platform,
  token: string,
  userId: string | null,
): Promise<DeviceRequestResponse> {
  const url = "device/register";
  const { data } = await axios.post(url, {
    platform,
    token,
    user_id: userId,
  });
  return data;
}

export async function unregisterToken(
  token: string,
): Promise<DeviceRequestResponse> {
  const url = "device/unregister";
  const { data } = await axios.delete(url, { data: { token } });
  return data;
}
