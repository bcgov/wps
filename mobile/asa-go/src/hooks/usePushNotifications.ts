import { useEffect, useRef, useState } from "react";
import {
  PushNotifications,
  PushNotificationSchema,
  Token,
  ActionPerformed,
} from "@capacitor/push-notifications";
import { PluginListenerHandle } from "@capacitor/core";

export interface UsePushNotificationsResult {
  token: string | null;
  notifications: PushNotificationSchema[];
  error: string | null;
}

export const usePushNotifications = (): UsePushNotificationsResult => {
  const [token, setToken] = useState<string | null>(null);
  const [notifications, setNotifications] = useState<PushNotificationSchema[]>(
    []
  );
  const [error, setError] = useState<string | null>(null);
  const listenersRef = useRef<PluginListenerHandle[]>([]);

  useEffect(() => {
    const initPush = async () => {
      console.log("[Push] Initializing");

      try {
        // check existing permission
        const permissionStatus = await PushNotifications.checkPermissions();

        // request if not granted
        if (permissionStatus.receive !== "granted") {
          const result = await PushNotifications.requestPermissions();
          if (result.receive !== "granted") {
            console.warn("[Push] Permission not granted");
            setError("Push notification permission not granted");
            return;
          }
        }

        // register with APNs / FCM
        await PushNotifications.register();

        // event listeners
        const regHandle = await PushNotifications.addListener(
          "registration",
          (token: Token) => {
            console.log("[Push] Registration success:", token.value);
            setToken(token.value);
          }
        );
        listenersRef.current.push(regHandle);

        const errHandle = await PushNotifications.addListener(
          "registrationError",
          (err) => {
            console.error("[Push] Registration error:", err);
            setError(JSON.stringify(err));
          }
        );
        listenersRef.current.push(errHandle);

        const receivedHandle = await PushNotifications.addListener(
          "pushNotificationReceived",
          (notification: PushNotificationSchema) => {
            console.log("[Push] Notification received:", notification);
            setNotifications((prev) => [...prev, notification]);
          }
        );
        listenersRef.current.push(receivedHandle);

        const actionHandle = await PushNotifications.addListener(
          "pushNotificationActionPerformed",
          (action: ActionPerformed) => {
            console.log("[Push] Action performed:", action);
          }
        );
        listenersRef.current.push(actionHandle);
      } catch (err: unknown) {
        console.error("[Push] Init error:", err);
        setError((err as Error).message ?? "Unknown error");
      }
    };

    initPush();

    // cleanup listeners on unmount
    return () => {
      (async () => {
        for (const listener of listenersRef.current) {
          try {
            await listener.remove();
          } catch (err) {
            console.warn("[Push] Error removing listener:", err);
          }
        }
        listenersRef.current = [];
      })();
    };
  }, []);

  return { token, notifications, error };
};
