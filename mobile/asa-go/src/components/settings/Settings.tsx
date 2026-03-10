import { FireCentreFireZoneUnits } from "@/api/fbaAPI";
import SubscriptionAccordion from "@/components/settings/SubscriptionAccordion";
import {
  fetchFireCentreInfo,
  initPinnedFireCentre,
} from "@/slices/settingsSlice";
import { AppDispatch, selectNetworkStatus, selectSettings } from "@/store";
import { theme } from "@/theme";
import { Alert, AlertTitle, Box, Button, Typography } from "@mui/material";
import { isNil } from "lodash";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { FirebaseMessaging } from "@capacitor-firebase/messaging";
import { PermissionState } from "@capacitor/core";

type ReceivePermission = PermissionState | "unknown";

const Settings = () => {
  const dispatch: AppDispatch = useDispatch();
  const { networkStatus } = useSelector(selectNetworkStatus);
  const { fireCentreFireZoneUnits, pinnedFireCentre } =
    useSelector(selectSettings);

  const [receivePermission, setReceivePermission] =
    useState<ReceivePermission>("unknown");
  const [checkingPerm, setCheckingPerm] = useState<boolean>(false);

  const notificationSettingsDisabled =
    receivePermission !== "granted" || !networkStatus.connected;

  // Load fire centres on mount
  useEffect(() => {
    dispatch(initPinnedFireCentre());
    dispatch(fetchFireCentreInfo());
  }, [dispatch]);

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
    refreshNotificationPermission();
  }, [refreshNotificationPermission]);

  // Derived ordered list of centres for display (memoized)
  const orderedFireCentres = useMemo<FireCentreFireZoneUnits[]>(() => {
    if (!fireCentreFireZoneUnits) return [];

    const sorted = fireCentreFireZoneUnits.toSorted((a, b) =>
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
  }, [fireCentreFireZoneUnits, pinnedFireCentre]);

  const renderNotificationMessage = () => {
    if (!networkStatus.connected || receivePermission !== "granted") {
      return;
    }
    return (
      <Typography
        sx={{ color: theme.palette.primary.main, padding: theme.spacing(1) }}
        variant="body1"
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
      <Typography
        sx={{ color: theme.palette.primary.main, padding: theme.spacing(1) }}
        variant="body1"
      >
        Notification settings are not available while offline.
      </Typography>
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

  const renderSettings = () => (
    <Box
      sx={{
        display: "flex",
        flex: 1,
        minHeight: 0,
        overflowY: "auto",
        flexDirection: "column",
      }}
    >
      {orderedFireCentres.map((unit) => (
        <SubscriptionAccordion
          key={unit.fire_centre_name}
          fireCentreFireZoneUnits={unit}
          disabled={notificationSettingsDisabled}
        />
      ))}
    </Box>
  );

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
      {renderPermissionBanner()}
      {renderOfflineMessage()}
      {renderNotificationMessage()}
      {renderSettings()}
    </Box>
  );
};

export default Settings;
