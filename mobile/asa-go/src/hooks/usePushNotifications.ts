import { useCallback, useEffect, useRef, useState } from "react";
import { PushNotificationService } from "@/services/pushNotificationService";

export function usePushNotifications() {
  const [token, setToken] = useState<string | null>(null);
  const serviceRef = useRef<PushNotificationService | null>(null);

  const initPushNotifications = useCallback(async () => {
    // Prevent multiple initializations of the same service
    if (serviceRef.current) {
      return;
    }

    const service = new PushNotificationService({
      onRegister: (t) => {
        setToken(t);
      },
      onNotificationReceived: (_evt) => {
        if (_evt) console.log(_evt.notification.body);
      },
      onNotificationAction: (_evt) => {
        if (_evt) console.log(_evt.notification.body);
      },
      onError: (err) => {
        console.error("Push notification error:", err);
      },
      androidChannel: {
        id: "general",
        name: "General",
        description: "General notifications",
        importance: 4, // Importance.High
        sound: "default",
      },
    });

    serviceRef.current = service;
    await service.initPushNotificationService();
  }, []);

  useEffect(() => {
    return () => {
      serviceRef.current?.unregister();
    };
  }, []);

  return { initPushNotifications, token };
}
