/**
 * React hook for managing push notifications
 */

import { useState, useEffect, useCallback } from "react";
import {
  pushNotificationService,
  NotificationPreferences,
  LocationUpdate,
} from "../services/pushNotificationService";

export interface UsePushNotificationsReturn {
  isInitialized: boolean;
  isEnabled: boolean;
  deviceToken: string | null;
  initialize: () => Promise<void>;
  updatePreferences: (
    preferences: Partial<NotificationPreferences>
  ) => Promise<void>;
  updateLocation: (location: LocationUpdate) => Promise<void>;
  checkPermissions: () => Promise<boolean>;
  error: string | null;
}

export const usePushNotifications = (): UsePushNotificationsReturn => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [isEnabled, setIsEnabled] = useState(false);
  const [deviceToken, setDeviceToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Initialize push notifications
  const initialize = useCallback(async () => {
    try {
      setError(null);
      await pushNotificationService.initialize();
      setIsInitialized(true);

      // Get device token after initialization
      const token = pushNotificationService.getDeviceToken();
      setDeviceToken(token);

      // Check if notifications are enabled
      const enabled = await pushNotificationService.areNotificationsEnabled();
      setIsEnabled(enabled);
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to initialize push notifications";
      setError(errorMessage);
      console.error("Push notification initialization failed:", err);
    }
  }, []);

  // Update notification preferences
  const updatePreferences = useCallback(
    async (preferences: Partial<NotificationPreferences>) => {
      try {
        setError(null);
        await pushNotificationService.updatePreferences(preferences);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to update preferences";
        setError(errorMessage);
        throw err;
      }
    },
    []
  );

  // Update device location
  const updateLocation = useCallback(async (location: LocationUpdate) => {
    try {
      setError(null);
      await pushNotificationService.updateLocation(location);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to update location";
      setError(errorMessage);
      throw err;
    }
  }, []);

  // Check notification permissions
  const checkPermissions = useCallback(async () => {
    try {
      const enabled = await pushNotificationService.areNotificationsEnabled();
      setIsEnabled(enabled);
      return enabled;
    } catch (err) {
      console.error("Failed to check notification permissions:", err);
      return false;
    }
  }, []);

  // Initialize on mount
  useEffect(() => {
    initialize();
  }, [initialize]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      pushNotificationService.removeAllListeners();
    };
  }, []);

  return {
    isInitialized,
    isEnabled,
    deviceToken,
    initialize,
    updatePreferences,
    updateLocation,
    checkPermissions,
    error,
  };
};
