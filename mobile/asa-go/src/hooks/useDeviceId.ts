import { Device } from "@capacitor/device";
import { useEffect, useState } from "react";

export function useDeviceId(): string | null {
  const [deviceId, setDeviceId] = useState<string | null>(null);

  useEffect(() => {
    Device.getId()
      .then(({ identifier }) => setDeviceId(identifier))
      .catch((e) => console.error(`Failed to get device ID: ${e}`));
  }, []);

  return deviceId;
}
