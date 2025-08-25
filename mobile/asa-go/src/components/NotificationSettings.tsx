/**
 * Push Notification Settings Component
 *
 * This component allows users to configure their push notification preferences
 */

import React, { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  FormGroup,
  FormControlLabel,
  Switch,
  Typography,
  Alert,
  Box,
  Button,
  Snackbar,
} from "@mui/material";
import { Notifications, NotificationsOff } from "@mui/icons-material";
import { usePushNotifications } from "../hooks/usePushNotifications";
import { NotificationPreferences } from "../services/pushNotificationService";

interface NotificationSettingsProps {
  onPreferencesChange?: (preferences: Partial<NotificationPreferences>) => void;
}

export const NotificationSettings: React.FC<NotificationSettingsProps> = ({
  onPreferencesChange,
}) => {
  const {
    isInitialized,
    isEnabled,
    deviceToken,
    updatePreferences,
    checkPermissions,
    error: hookError,
  } = usePushNotifications();

  const [preferences, setPreferences] = useState<NotificationPreferences>({
    weatherAlertsEnabled: true,
    fireAlertsEnabled: true,
    generalNotificationsEnabled: true,
    enabled: true,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Update local preferences and notify parent
  const handlePreferenceChange = (key: keyof NotificationPreferences) => {
    return (event: React.ChangeEvent<HTMLInputElement>) => {
      const newPreferences = {
        ...preferences,
        [key]: event.target.checked,
      };
      setPreferences(newPreferences);
      onPreferencesChange?.(newPreferences);
    };
  };

  // Save preferences to server
  const handleSavePreferences = async () => {
    if (!isInitialized || !deviceToken) {
      setError("Push notifications are not properly initialized");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await updatePreferences(preferences);
      setSuccessMessage("Notification preferences saved successfully");
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to save preferences";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Refresh permission status
  const handleRefreshPermissions = async () => {
    setIsLoading(true);
    try {
      await checkPermissions();
    } catch (err) {
      console.error("Failed to check permissions:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Close snackbar
  const handleCloseSnackbar = () => {
    setSuccessMessage(null);
    setError(null);
  };

  // Display current error (from hook or component)
  const currentError = hookError || error;

  if (!isInitialized) {
    return (
      <Card>
        <CardHeader title="Push Notifications" />
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            Initializing push notifications...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader
          title={
            <Box display="flex" alignItems="center" gap={1}>
              {isEnabled ? (
                <Notifications color="primary" />
              ) : (
                <NotificationsOff color="disabled" />
              )}
              <Typography variant="h6">Push Notifications</Typography>
            </Box>
          }
        />
        <CardContent>
          {!isEnabled && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Push notifications are disabled. Please enable them in your device
              settings to receive alerts.
              <Box mt={1}>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={handleRefreshPermissions}
                  disabled={isLoading}
                >
                  Check Again
                </Button>
              </Box>
            </Alert>
          )}

          {currentError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {currentError}
            </Alert>
          )}

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Configure which types of notifications you want to receive from the
            WPS app.
          </Typography>

          <FormGroup>
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.enabled}
                  onChange={handlePreferenceChange("enabled")}
                  disabled={!isEnabled || isLoading}
                />
              }
              label="Enable All Notifications"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={
                    preferences.weatherAlertsEnabled && preferences.enabled
                  }
                  onChange={handlePreferenceChange("weatherAlertsEnabled")}
                  disabled={!isEnabled || !preferences.enabled || isLoading}
                />
              }
              label="Weather Alerts"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={preferences.fireAlertsEnabled && preferences.enabled}
                  onChange={handlePreferenceChange("fireAlertsEnabled")}
                  disabled={!isEnabled || !preferences.enabled || isLoading}
                />
              }
              label="Fire Alerts"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={
                    preferences.generalNotificationsEnabled &&
                    preferences.enabled
                  }
                  onChange={handlePreferenceChange(
                    "generalNotificationsEnabled"
                  )}
                  disabled={!isEnabled || !preferences.enabled || isLoading}
                />
              }
              label="General Notifications"
            />
          </FormGroup>

          {deviceToken && (
            <Box mt={2}>
              <Typography variant="caption" color="text.secondary">
                Device ID: {deviceToken.substring(0, 8)}...
              </Typography>
            </Box>
          )}

          <Box mt={2} display="flex" gap={1}>
            <Button
              variant="contained"
              onClick={handleSavePreferences}
              disabled={!isEnabled || isLoading}
            >
              {isLoading ? "Saving..." : "Save Preferences"}
            </Button>

            <Button
              variant="outlined"
              onClick={handleRefreshPermissions}
              disabled={isLoading}
            >
              Refresh Status
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Snackbar
        open={!!successMessage}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
      >
        <Alert onClose={handleCloseSnackbar} severity="success">
          {successMessage}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
      >
        <Alert onClose={handleCloseSnackbar} severity="error">
          {error}
        </Alert>
      </Snackbar>
    </>
  );
};
