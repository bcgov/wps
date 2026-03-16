import { FireCentreInfo } from "@/api/fbaAPI";
import SubscriptionAccordion from "@/components/settings/SubscriptionAccordion";
import {
  fetchFireCentreInfo,
  initPinnedFireCentre,
  initSubscriptions,
} from "@/slices/settingsSlice";
import { AppDispatch, selectNetworkStatus, selectSettings } from "@/store";
import { theme } from "@/theme";
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  LinearProgress,
  Typography,
} from "@mui/material";
import { isNil } from "lodash";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { useAppIsActive } from "@/hooks/useAppIsActive";
import { NavPanel } from "@/utils/constants";
import { FirebaseMessaging } from "@capacitor-firebase/messaging";
import { PermissionState } from "@capacitor/core";

type ReceivePermission = PermissionState | "unknown";

interface SettingsProps {
  activeTab: NavPanel;
}

const Settings = ({ activeTab }: SettingsProps) => {
  const dispatch: AppDispatch = useDispatch();
  const isActive = useAppIsActive();
  const isVisible = activeTab === NavPanel.SETTINGS;

  const { networkStatus } = useSelector(selectNetworkStatus);
  const { fireCentreInfos, loading, error, pinnedFireCentre } =
    useSelector(selectSettings);

  const [receivePermission, setReceivePermission] =
    useState<ReceivePermission>("unknown");
  const [checkingPerm, setCheckingPerm] = useState<boolean>(false);

  const notificationSettingsDisabled =
    receivePermission !== "granted" || !networkStatus.connected;

  // Load subscriptions and pinned fire centre from locally cached user preferences
  useEffect(() => {
    dispatch(initPinnedFireCentre());
    dispatch(initSubscriptions());
  }, [dispatch]);

  // Fetch fire centre info on mount or anytime the app is foregrounded
  useEffect(() => {
    dispatch(fetchFireCentreInfo());
  }, [isActive, dispatch]);

  // Check push notification permission
  const refreshNotificationPermission = useCallback(async () => {
    try {
      setCheckingPerm(true);
      const res = await FirebaseMessaging.checkPermissions();
      setReceivePermission(res.receive ?? "unknown");
    } catch (err) {
      // If the plugin throws (rare), mark as unknown but don't break the UI
      setReceivePermission("unknown");
      console.error("checkPermissions failed", err);
    } finally {
      setCheckingPerm(false);
    }
  }, []);

  // Check push notification settings on mount
  useEffect(() => {
    if (isVisible) {
      refreshNotificationPermission();
    }
  }, [refreshNotificationPermission, isVisible]);

  // Derived ordered list of centres for display (memoized)
  const orderedFireCentres = useMemo<FireCentreInfo[]>(() => {
    if (!fireCentreInfos) return [];

    const sorted = fireCentreInfos.toSorted((a, b) =>
      a.fire_centre_name.localeCompare(b.fire_centre_name),
    );

    if (!isNil(pinnedFireCentre)) {
      // Move pinned item to the top
      const index = sorted.findIndex(
        (fc) => fc.fire_centre_name === pinnedFireCentre,
      );

      if (index > 0) {
        const [item] = sorted.splice(index, 1);
        sorted.unshift(item);
      }
    }

    return sorted;
  }, [fireCentreInfos, pinnedFireCentre]);

  const renderNotificationMessage = () => {
    if (!networkStatus.connected || receivePermission !== "granted" || error) {
      return;
    }
    return (
      <Typography
        sx={{
          color: theme.palette.primary.main,
          padding: theme.spacing(2),
        }}
        variant="body2"
      >
        Set your notification subscriptions.
      </Typography>
    );
  };

  const renderOfflineMessage = () => {
    if (networkStatus.connected) {
      return;
    }

    return (
      <Alert
        severity="warning"
        sx={{ mx: 1, my: 1 }}
        data-testid="notifications-permission-warning"
      >
        <AlertTitle>Offline</AlertTitle>
        Notification settings are not available while offline.
      </Alert>
    );
  };

  const renderPermissionBanner = () => {
    // Show a banner if permission is not explicitly granted in system settings and we're online.
    const shouldShow =
      receivePermission !== "granted" && networkStatus.connected;
    if (shouldShow) {
      return (
        <Alert
          severity="warning"
          sx={{ mx: 1, my: 1 }}
          data-testid="notifications-permission-warning"
        >
          <AlertTitle>Push notifications disabled</AlertTitle>
          Notifications are currently disabled in your system settings. To
          receive alerts, enable notifications for this app in your device
          settings.
          <Box mt={1} display="flex" gap={1}>
            <Button
              size="small"
              variant="outlined"
              onClick={refreshNotificationPermission}
              disabled={checkingPerm}
            >
              {checkingPerm ? "Checking…" : "Re-check"}
            </Button>
          </Box>
        </Alert>
      );
    }
  };

  const renderSettings = () => {
    if (loading) {
      return (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            padding: theme.spacing(2),
          }}
        >
          <Typography variant="body2" color="primary">
            Retrieving notification settings...
          </Typography>
          <LinearProgress color="primary" sx={{ pt: theme.spacing(1) }} />
        </Box>
      );
    }
    if (error) {
      return (
        <Alert
          severity="warning"
          sx={{ mx: 1, my: 1 }}
          data-testid="settings-error-alert"
        >
          <AlertTitle>Error</AlertTitle>
          An error occurred when attempting to retrieve notification settings.
          Please check your network connection and reload the app.
        </Alert>
      );
    }
    return (
      <Box
        sx={{
          display: "flex",
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          flexDirection: "column",
        }}
      >
        {orderedFireCentres.map((unit, index) => (
          <SubscriptionAccordion
            key={unit.fire_centre_name}
            fireCentreInfo={unit}
            disabled={notificationSettingsDisabled}
            defaultExpanded={index === 0}
          />
        ))}
      </Box>
    );
  };

  return (
    <Box
      data-testid="asa-go-settings"
      sx={{
        background: "white",
        display: "flex",
        flex: 1,
        flexDirection: "column",
        height: "100%",
        overflow: "hidden",
      }}
    >
      <Box
        sx={{
          display: "flex",
          pl: theme.spacing(1),
          py: theme.spacing(1),
          borderBottomColor: "rgba(0,0,0,0.1)",
          borderBottomWidth: "1px",
          borderBottomStyle: "solid",
        }}
      >
        <Box
          sx={{
            backgroundColor: theme.palette.primary.main,
            borderRadius: "24px",
            display: "inline-flex",
          }}
        >
          <Typography
            variant="body2"
            sx={{
              color: "white",
              px: theme.spacing(2),
              py: theme.spacing(0.5),
            }}
          >
            Notifications
          </Typography>
        </Box>
      </Box>
      {renderPermissionBanner()}
      {renderOfflineMessage()}
      {renderNotificationMessage()}
      {renderSettings()}
    </Box>
  );
};

export default Settings;
