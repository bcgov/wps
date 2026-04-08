import { useCallback, useEffect, useRef } from "react";
import { PushNotificationService } from "@/services/pushNotificationService";
import {
  registerDevice,
  setCurrentFcmToken,
} from "@/slices/pushNotificationSlice";
import { type AppDispatch } from "@/store";
import { useDispatch } from "react-redux";

export function usePushNotifications() {
  const dispatch: AppDispatch = useDispatch();
  const serviceRef = useRef<PushNotificationService | null>(null);

  const initPushNotifications = useCallback(async () => {
    // Prevent multiple initializations of the same service
    if (serviceRef.current) {
      return;
    }

    const service = new PushNotificationService({
      onRegister: (t) => {
        dispatch(setCurrentFcmToken(t));
        dispatch(registerDevice());
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
  }, [dispatch]);

  useEffect(() => {
    return () => {
      serviceRef.current?.unregister();
    };
  }, []);

  return { initPushNotifications };
}
