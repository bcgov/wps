import {
  Channel,
  FirebaseMessaging,
  Importance,
  NotificationActionPerformedEvent,
  NotificationReceivedEvent,
  PermissionStatus,
  TokenReceivedEvent,
} from "@capacitor-firebase/messaging";
import { PluginListenerHandle } from "@capacitor/core";

export type PushInitOptions = {
  onRegister?: (token: string) => void;
  onNotificationReceived?: (evt: NotificationReceivedEvent) => void;
  onNotificationAction?: (evt: NotificationActionPerformedEvent) => void;
  onError?: (err: unknown) => void;
  androidChannel?: Channel;
};

export class PushNotificationService {
  private handles: PluginListenerHandle[] = [];
  constructor(private readonly opts: PushInitOptions = {}) {}

  async initPushNotificationService(): Promise<void> {
    try {
      // 1) Permissions (Android 13+ & iOS)
      const check: PermissionStatus =
        await FirebaseMessaging.checkPermissions();
      if (check.receive !== "granted") {
        const req = await FirebaseMessaging.requestPermissions();
        if (req.receive !== "granted")
          throw new Error("Push permission not granted");
      }
      // (Permissions + methods per plugin README) [1](https://dev.to/vaclav_svara_50ba53bc0010/firebase-push-notifications-in-capacitor-angular-apps-the-complete-implementation-guide-1c67)

      // 2) Android channel (recommended on 8+)
      await FirebaseMessaging.createChannel(
        this.opts.androidChannel ?? {
          id: "general",
          name: "General",
          description: "General notifications",
          importance: Importance.High,
          sound: "default",
        },
      ); // (Channel API from plugin) [1](https://dev.to/vaclav_svara_50ba53bc0010/firebase-push-notifications-in-capacitor-angular-apps-the-complete-implementation-guide-1c67)

      // 3) FCM token (works on iOS & Android)
      const { token } = await FirebaseMessaging.getToken();
      this.opts.onRegister?.(token); // (getToken returns { token }) [1](https://dev.to/vaclav_svara_50ba53bc0010/firebase-push-notifications-in-capacitor-angular-apps-the-complete-implementation-guide-1c67)

      // 4) Strongly-typed listeners
      const tokenReceivedHandler = await FirebaseMessaging.addListener(
        "tokenReceived",
        (e: TokenReceivedEvent) => {
          console.log("tokenReceivedHandler called");
          this.opts.onRegister?.(e.token);
        },
      );

      const notificationReceivedHandler = await FirebaseMessaging.addListener(
        "notificationReceived",
        (evt: NotificationReceivedEvent) => {
          this.opts.onNotificationReceived?.(evt);
        },
      );

      const onNotificationAction = await FirebaseMessaging.addListener(
        "notificationActionPerformed",
        (evt: NotificationActionPerformedEvent) => {
          this.opts.onNotificationAction?.(evt);
        },
      );

      this.handles.push(
        tokenReceivedHandler,
        notificationReceivedHandler,
        onNotificationAction,
      );
    } catch (err) {
      this.opts.onError?.(err);
      throw err;
    }
  }

  async unregister(): Promise<void> {
    try {
      await FirebaseMessaging.removeAllListeners(); // (plugin cleanup) [1](https://dev.to/vaclav_svara_50ba53bc0010/firebase-push-notifications-in-capacitor-angular-apps-the-complete-implementation-guide-1c67)
    } catch {
      /* noop */
    } finally {
      await Promise.all(
        this.handles.map(async (h) => {
          try {
            await h.remove();
          } catch {
            /* noop */
          }
        }),
      );
      this.handles = [];
    }
  }
}
