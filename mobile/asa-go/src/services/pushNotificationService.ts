import {
  Channel,
  FirebaseMessaging,
  Importance,
  NotificationActionPerformedEvent,
  NotificationReceivedEvent,
  PermissionStatus,
  TokenReceivedEvent,
} from "@capacitor-firebase/messaging";
import { Capacitor, PluginListenerHandle } from "@capacitor/core";

export type PushInitOptions = {
  onRegister?: (token: string) => void;
  onNotificationReceived?: (evt: NotificationReceivedEvent) => void;
  onNotificationAction?: (evt: NotificationActionPerformedEvent) => void;
  onError?: (err: unknown) => void;
  androidChannel?: Channel;
};

export class PushNotificationService {
  private handles: PluginListenerHandle[] = [];
  private isInitialized = false;

  constructor(private readonly opts: PushInitOptions = {}) {}

  async initPushNotificationService(): Promise<void> {
    if (this.isInitialized) {
      return;
    }
    try {
      // Permissions (Android 13+ & iOS)
      const check: PermissionStatus =
        await FirebaseMessaging.checkPermissions();
      if (check.receive !== "granted") {
        const req = await FirebaseMessaging.requestPermissions();
        if (req.receive !== "granted")
          throw new Error("Push permission not granted");
      }

      // Android channel (recommended on 8+)
      if (Capacitor.getPlatform() === "android") {
        await FirebaseMessaging.createChannel(
          this.opts.androidChannel ?? {
            id: "general",
            name: "General",
            description: "General notifications",
            importance: Importance.High,
            sound: "default",
          },
        );
      }

      // FCM token (works on iOS & Android)
      const { token } = await FirebaseMessaging.getToken();
      this.opts.onRegister?.(token);

      // Strongly-typed listeners
      const tokenReceivedHandler = await FirebaseMessaging.addListener(
        "tokenReceived",
        (e: TokenReceivedEvent) => {
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
    } catch (e) {
      console.error(e);
      this.opts.onError?.(e);
    } finally {
      this.isInitialized = true;
    }
  }

  async unregister(): Promise<void> {
    try {
      await FirebaseMessaging.removeAllListeners();
    } catch (e) {
      console.error(e);
      /* noop */
    } finally {
      await Promise.all(
        this.handles.map(async (h) => {
          try {
            await h.remove();
          } catch (e) {
            console.error(e);
            /* noop */
          }
        }),
      );
      this.handles = [];
      this.isInitialized = false;
    }
  }
}
