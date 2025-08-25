/**
 * Push Notification Service for iOS
 *
 * This service handles push notification registration, permissions,
 * and communication with the WPS API server.
 */

import {
  PushNotifications,
  Token,
  PushNotificationSchema,
  ActionPerformed,
} from "@capacitor/push-notifications";
import { Capacitor } from "@capacitor/core";
import axios from "axios";
import { Device } from "@capacitor/device";

// Types for push notification management
export interface DeviceRegistration {
  deviceToken: string;
  userId?: string;
  deviceName?: string;
  deviceModel?: string;
  osVersion?: string;
  appVersion?: string;
  environment?: string;
}

export interface NotificationPreferences {
  weatherAlertsEnabled: boolean;
  fireAlertsEnabled: boolean;
  generalNotificationsEnabled: boolean;
  enabled: boolean;
}

export interface LocationUpdate {
  latitude: string;
  longitude: string;
  locationName?: string;
}

export type NotificationType =
  | "weather_alert"
  | "fire_alert"
  | "general"
  | "background_update";

export interface NotificationPayload {
  type: NotificationType;
  title?: string;
  body?: string;
  weather_data?: Record<string, unknown>;
  fire_data?: Record<string, unknown>;
  priority?: string;
  [key: string]: unknown;
}

class PushNotificationService {
  private isInitialized = false;
  private deviceToken: string | null = null;
  private apiBaseUrl: string;
  private environment: string;

  constructor() {
    // Configure based on environment
    this.environment =
      process.env.NODE_ENV === "development" ? "development" : "production";
    this.apiBaseUrl =
      process.env.VITE_API_BASE_URL || "https://your-api-domain.com";
  }

  /**
   * Initialize push notifications
   * This should be called when the app starts
   */
  async initialize(): Promise<void> {
    if (this.isInitialized || !Capacitor.isNativePlatform()) {
      return;
    }

    try {
      // Request permission to use push notifications
      // iOS will prompt user to allow notifications
      let permissionStatus = await PushNotifications.checkPermissions();

      if (permissionStatus.receive === "prompt") {
        permissionStatus = await PushNotifications.requestPermissions();
      }

      if (permissionStatus.receive !== "granted") {
        console.warn("Push notification permission not granted");
        return;
      }

      // Register with Apple Push Notification Service
      await PushNotifications.register();

      // Set up event listeners
      this.setupEventListeners();

      this.isInitialized = true;
      console.log("Push notifications initialized successfully");
    } catch (error) {
      console.error("Error initializing push notifications:", error);
      throw error;
    }
  }

  /**
   * Set up push notification event listeners
   */
  private setupEventListeners(): void {
    // Called when the app successfully registers for push notifications
    PushNotifications.addListener("registration", async (token: Token) => {
      console.log("Push registration success, token: ", token.value);
      this.deviceToken = token.value;

      // Register device with your server
      await this.registerDeviceWithServer(token.value);
    });

    // Called when the app fails to register for push notifications
    PushNotifications.addListener(
      "registrationError",
      (error: { error: string }) => {
        console.error("Push registration error: ", error.error);
      }
    );

    // Called when a push notification is received while app is in foreground
    PushNotifications.addListener(
      "pushNotificationReceived",
      (notification: PushNotificationSchema) => {
        console.log("Push notification received: ", notification);
        this.handleForegroundNotification(notification);
      }
    );

    // Called when a user taps on a push notification
    PushNotifications.addListener(
      "pushNotificationActionPerformed",
      (notification: ActionPerformed) => {
        console.log("Push notification action performed: ", notification);
        this.handleNotificationAction(notification);
      }
    );
  }

  /**
   * Register device with the server
   */
  private async registerDeviceWithServer(deviceToken: string): Promise<void> {
    try {
      const deviceInfo = await Device.getInfo();

      const registrationData: DeviceRegistration = {
        deviceToken,
        deviceName: deviceInfo.name || "Unknown Device",
        deviceModel: deviceInfo.model || "Unknown Model",
        osVersion: deviceInfo.osVersion || "Unknown Version",
        appVersion: process.env.VITE_APP_VERSION || "1.0.0",
        environment: this.environment,
      };

      const response = await axios.post(
        `${this.apiBaseUrl}/push-notifications/register`,
        registrationData,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      console.log("Device registered with server:", response.data);
    } catch (error) {
      console.error("Failed to register device with server:", error);
      // Don't throw here - app should continue working even if server registration fails
    }
  }

  /**
   * Update notification preferences
   */
  async updatePreferences(
    preferences: Partial<NotificationPreferences>
  ): Promise<void> {
    if (!this.deviceToken) {
      console.warn("No device token available for preference update");
      return;
    }

    try {
      const updateData = {
        device_token: this.deviceToken,
        environment: this.environment,
        ...preferences,
      };

      await axios.put(
        `${this.apiBaseUrl}/push-notifications/preferences`,
        updateData,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      console.log("Notification preferences updated");
    } catch (error) {
      console.error("Failed to update notification preferences:", error);
      throw error;
    }
  }

  /**
   * Update device location for geo-targeted notifications
   */
  async updateLocation(location: LocationUpdate): Promise<void> {
    if (!this.deviceToken) {
      console.warn("No device token available for location update");
      return;
    }

    try {
      const updateData = {
        device_token: this.deviceToken,
        environment: this.environment,
        ...location,
      };

      await axios.put(
        `${this.apiBaseUrl}/push-notifications/location`,
        updateData,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      console.log("Device location updated");
    } catch (error) {
      console.error("Failed to update device location:", error);
      throw error;
    }
  }

  /**
   * Handle notification received while app is in foreground
   */
  private handleForegroundNotification(
    notification: PushNotificationSchema
  ): void {
    const payload = this.parseNotificationPayload(notification.data);

    switch (payload.type) {
      case "weather_alert":
        this.handleWeatherAlert(notification, payload);
        break;
      case "fire_alert":
        this.handleFireAlert(notification, payload);
        break;
      case "general":
        this.handleGeneralNotification(notification, payload);
        break;
      case "background_update":
        this.handleBackgroundUpdate(payload);
        break;
      default:
        console.log("Unknown notification type:", payload.type);
    }
  }

  /**
   * Handle notification tap/action
   */
  private handleNotificationAction(actionPerformed: ActionPerformed): void {
    const notification = actionPerformed.notification;
    const payload = this.parseNotificationPayload(notification.data);

    console.log("User tapped notification:", payload);

    // Navigate to appropriate screen based on notification type
    switch (payload.type) {
      case "weather_alert":
        this.navigateToWeatherScreen(payload);
        break;
      case "fire_alert":
        this.navigateToFireScreen(payload);
        break;
      case "general":
        this.navigateToHomeScreen();
        break;
      default:
        this.navigateToHomeScreen();
    }
  }

  /**
   * Parse notification payload
   */
  private parseNotificationPayload(data: unknown): NotificationPayload {
    try {
      // The data might be a string that needs parsing or already an object
      if (typeof data === "string") {
        return JSON.parse(data);
      }
      return data as NotificationPayload;
    } catch (error) {
      console.error("Failed to parse notification payload:", error);
      return { type: "general" };
    }
  }

  /**
   * Handle weather alert notification
   */
  private handleWeatherAlert(
    notification: PushNotificationSchema,
    payload: NotificationPayload
  ): void {
    console.log("Weather alert received:", payload);

    // Show in-app alert or banner
    this.showInAppAlert({
      title: notification.title || "Weather Alert",
      body: notification.body || "Check the latest weather conditions",
      type: "weather",
      data: payload.weather_data,
    });
  }

  /**
   * Handle fire alert notification
   */
  private handleFireAlert(
    notification: PushNotificationSchema,
    payload: NotificationPayload
  ): void {
    console.log("Fire alert received:", payload);

    // Show high-priority in-app alert
    this.showInAppAlert({
      title: notification.title || "Fire Alert",
      body: notification.body || "Fire activity detected in your area",
      type: "fire",
      priority: "high",
      data: payload.fire_data,
    });
  }

  /**
   * Handle general notification
   */
  private handleGeneralNotification(
    notification: PushNotificationSchema,
    payload: NotificationPayload
  ): void {
    console.log("General notification received:", payload);

    // Show standard in-app notification
    this.showInAppAlert({
      title: notification.title || "Notification",
      body: notification.body || "You have a new notification",
      type: "general",
    });
  }

  /**
   * Handle background update notification
   */
  private handleBackgroundUpdate(payload: NotificationPayload): void {
    console.log("Background update received:", payload);

    // Trigger data refresh or app state update
    // This could trigger Redux actions to update app state
    this.triggerDataRefresh(payload);
  }

  /**
   * Show in-app alert (to be implemented based on your UI framework)
   */
  private showInAppAlert(alert: {
    title: string;
    body: string;
    type: string;
    priority?: string;
    data?: Record<string, unknown>;
  }): void {
    // TODO: Implement based on your UI framework (React, native alerts, etc.)
    // For now, just log
    console.log("Showing in-app alert:", alert);

    // Example: If using a notification toast library
    // toast.show({
    //   type: alert.priority === 'high' ? 'error' : 'info',
    //   title: alert.title,
    //   message: alert.body,
    //   duration: alert.priority === 'high' ? 0 : 5000 // 0 = persistent for high priority
    // });
  }

  /**
   * Navigation helpers (to be implemented based on your routing)
   */
  private navigateToWeatherScreen(payload: NotificationPayload): void {
    // TODO: Implement navigation to weather screen
    // Example: router.push('/weather', { data: payload.weather_data });
    console.log("Navigate to weather screen with data:", payload.weather_data);
  }

  private navigateToFireScreen(payload: NotificationPayload): void {
    // TODO: Implement navigation to fire screen
    // Example: router.push('/fire-alerts', { data: payload.fire_data });
    console.log("Navigate to fire screen with data:", payload.fire_data);
  }

  private navigateToHomeScreen(): void {
    // TODO: Implement navigation to home screen
    // Example: router.push('/');
    console.log("Navigate to home screen");
  }

  /**
   * Trigger data refresh based on background update
   */
  private triggerDataRefresh(payload: NotificationPayload): void {
    // TODO: Implement data refresh logic
    // This could dispatch Redux actions or call API methods
    console.log("Triggering data refresh for:", payload);

    // Example:
    // store.dispatch(refreshWeatherData());
    // store.dispatch(refreshFireData());
  }

  /**
   * Check if push notifications are available and enabled
   */
  async areNotificationsEnabled(): Promise<boolean> {
    if (!Capacitor.isNativePlatform()) {
      return false;
    }

    try {
      const status = await PushNotifications.checkPermissions();
      return status.receive === "granted";
    } catch (error) {
      console.error("Failed to check notification permissions:", error);
      return false;
    }
  }

  /**
   * Get the current device token
   */
  getDeviceToken(): string | null {
    return this.deviceToken;
  }

  /**
   * Remove push notification listeners (useful for cleanup)
   */
  removeAllListeners(): void {
    PushNotifications.removeAllListeners();
    this.isInitialized = false;
    this.deviceToken = null;
  }
}

// Export singleton instance
export const pushNotificationService = new PushNotificationService();

// Export the class for testing purposes
export { PushNotificationService };
