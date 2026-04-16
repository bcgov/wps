import { useAppIsActive } from "@/hooks/useAppIsActive";
import {
  MAX_REGISTRATION_ATTEMPTS,
  registerDevice,
  resetRegistrationAttempts,
  setPendingNotificationData,
  setRegistrationError,
} from "@/slices/pushNotificationSlice";
import {
  AppDispatch,
  selectNetworkStatus,
  selectPushNotification,
} from "@/store";
import { PushNotificationData } from "@/types/asaGoTypes";
import {
  FirebaseMessaging,
  Importance,
  NotificationActionPerformedEvent,
  NotificationReceivedEvent,
  PermissionStatus,
  TokenReceivedEvent,
} from "@capacitor-firebase/messaging";
import { Capacitor, PluginListenerHandle } from "@capacitor/core";
import {
  ActionPerformed,
  LocalNotifications,
} from "@capacitor/local-notifications";
import { useCallback, useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

const ANDROID_CHANNEL = {
  id: "general",
  name: "General",
  description: "General notifications",
  importance: Importance.High,
  sound: "default",
};

export function usePushNotifications() {
  const [currentFcmToken, setCurrentFcmToken] = useState<string | null>(null);
  const handles = useRef<PluginListenerHandle[]>([]);
  const initialized = useRef(false);
  const dispatch = useDispatch<AppDispatch>();
  const { registrationError, registeredFcmToken, registrationAttempts } =
    useSelector(selectPushNotification);
  const { networkStatus } = useSelector(selectNetworkStatus);
  const isActive = useAppIsActive();

  const initPushNotifications = useCallback(async () => {
    if (initialized.current) return;
    try {
      const check: PermissionStatus =
        await FirebaseMessaging.checkPermissions();
      if (check.receive !== "granted") {
        const req = await FirebaseMessaging.requestPermissions();
        if (req.receive !== "granted") return;
      }

      if (Capacitor.getPlatform() === "android") {
        await FirebaseMessaging.createChannel(ANDROID_CHANNEL);
      }

      try {
        const { token } = await FirebaseMessaging.getToken();
        setCurrentFcmToken(token);
      } catch (e) {
        console.error("Failed to get FCM token during init:", e);
        dispatch(setRegistrationError(true));
        return;
      }

      const tokenHandle = await FirebaseMessaging.addListener(
        "tokenReceived",
        (e: TokenReceivedEvent) => setCurrentFcmToken(e.token),
      );

      const receivedHandle = await FirebaseMessaging.addListener(
        "notificationReceived",
        async (evt: NotificationReceivedEvent) => {
          if (Capacitor.getPlatform() === "android") {
            await LocalNotifications.schedule({
              notifications: [
                {
                  id: Math.floor(Math.random() * 0x80000000), // id needs to be a 32-bit int
                  title: evt.notification.title ?? "",
                  body: evt.notification.body ?? "",
                  channelId: ANDROID_CHANNEL.id,
                  extra: evt.notification.data,
                  group: "asa_go_alerts", // groups notifications together to mimic system notification grouping behaviour
                  groupSummary: false, // don't display a summary when > 3 notifications arrive, just group them
                },
              ],
            });
          }
        },
      );

      const actionHandle = await FirebaseMessaging.addListener(
        "notificationActionPerformed",
        (evt: NotificationActionPerformedEvent) => {
          const data = evt?.notification?.data as
            | PushNotificationData
            | undefined;
          if (data) {
            dispatch(setPendingNotificationData(data));
          }
        },
      );

      const localActionHandle = await LocalNotifications.addListener(
        "localNotificationActionPerformed",
        (evt: ActionPerformed) => {
          const data = evt?.notification?.extra as
            | PushNotificationData
            | undefined;
          if (data) {
            dispatch(setPendingNotificationData(data));
          }
        },
      );

      handles.current.push(
        tokenHandle,
        receivedHandle,
        actionHandle,
        localActionHandle,
      );
      initialized.current = true;
    } catch (e) {
      console.error("Push notification error:", e);
    }
  }, [dispatch]);

  useEffect(() => {
    if (networkStatus.connected && currentFcmToken) {
      dispatch(registerDevice(currentFcmToken, registeredFcmToken));
    }
  }, [
    currentFcmToken,
    registeredFcmToken,
    networkStatus.connected,
    isActive,
    dispatch,
  ]);

  const retryRegistration = useCallback(async () => {
    if (!registrationError) return;
    if (registrationAttempts >= MAX_REGISTRATION_ATTEMPTS) {
      // Caller is deliberately retrying, e.g. in settings and context drawer menu
      dispatch(resetRegistrationAttempts());
    }
    dispatch(setRegistrationError(false));
    try {
      const { token } = await FirebaseMessaging.getToken();
      if (token) dispatch(registerDevice(token, registeredFcmToken));
    } catch (e) {
      console.error("Failed to get token for retry:", e);
      dispatch(setRegistrationError(true));
    }
  }, [registrationError, registrationAttempts, registeredFcmToken, dispatch]);

  useEffect(() => {
    return () => {
      if (initialized.current) {
        void FirebaseMessaging.removeAllListeners();
      }
      handles.current.forEach((h) => void h.remove());
      handles.current = [];
      initialized.current = false;
    };
  }, []);

  return { initPushNotifications, retryRegistration };
}
