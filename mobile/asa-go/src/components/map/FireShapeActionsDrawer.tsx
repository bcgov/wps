import { FireShape } from "@/api/fbaAPI";
import { SwipeableBottomDrawer } from "@/components/SwipeableBottomDrawer";
import { useIsPortrait } from "@/hooks/useIsPortrait";
import { useIsTablet } from "@/hooks/useIsTablet";
import { checkPushNotificationPermission, registerDevice } from "@/slices/pushNotificationSlice";
import { useNotificationSettings } from "@/hooks/useNotificationSettings";
import {
  AppDispatch,
  selectNetworkStatus,
  selectNotificationSetupState,
  selectNotificationSettingsDisabled,
  selectPushNotification,
  selectSettings,
} from "@/store";
import { fireZoneUnitNameFormatter } from "@/utils/stringUtils";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import CloseIcon from "@mui/icons-material/Close";
import NotificationsActiveIcon from "@mui/icons-material/NotificationsActive";
import NotificationsNoneOutlinedIcon from "@mui/icons-material/NotificationsNoneOutlined";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import {
  Box,
  Button,
  CircularProgress,
  IconButton,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import NotificationErrorSnackbar from "@/components/NotificationErrorSnackbar";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { subscriptionUpdateErrorMessage } from "@/utils/constants";

interface FireShapeActionsDrawerProps {
  open: boolean;
  selectedFireShape: FireShape | undefined;
  onClose: () => void;
  onSelectProfile: () => void;
  onSelectAdvisory: () => void;
}

const FireShapeActionsDrawer = ({
  open,
  selectedFireShape,
  onClose,
  onSelectProfile,
  onSelectAdvisory,
}: FireShapeActionsDrawerProps) => {
  const dispatch: AppDispatch = useDispatch();
  const { toggleSubscription, updateError, clearUpdateError } =
    useNotificationSettings();
  const theme = useTheme();

  const isPortrait = useIsPortrait();
  const isTablet = useIsTablet();
  const isSmallScreen = useMediaQuery(theme.breakpoints.down("lg"));
  const useSideSheet = !isPortrait && isSmallScreen;

  const { subscriptions } = useSelector(selectSettings);
  const { pushNotificationPermission, deviceIdError, registeredFcmToken } = useSelector(
    selectPushNotification,
  );
  const { networkStatus } = useSelector(selectNetworkStatus);
  const setupState = useSelector(selectNotificationSetupState);
  const notificationSettingsDisabled = useSelector(
    selectNotificationSettingsDisabled,
  );

  const selectedFireShapeId = selectedFireShape?.fire_shape_id;
  const isSubscribed =
    selectedFireShapeId !== undefined &&
    subscriptions.includes(selectedFireShapeId);

  const isAwaitingToken =
    setupState === "unregistered" && networkStatus.connected && !deviceIdError;

  const actionIconSize = isTablet ? 40 : 32;
  const actionIconSx = { fontSize: actionIconSize };

  const actionButtonSx = {
    borderRadius: 2,
    flexDirection: "column",
    fontSize: isTablet ? "20px" : "14px",
    gap: 0.75,
    padding: 1,
    textTransform: "none",
  };

  useEffect(() => {
    // Refresh permission state when the drawer opens so the subscribe action is accurate
    if (open && pushNotificationPermission === "unknown") {
      dispatch(checkPushNotificationPermission());
    }
  }, [dispatch, open, pushNotificationPermission]);

  useEffect(() => {
    if (open) {
      dispatch(registerDevice(registeredFcmToken));
    }
  }, [dispatch, open, registeredFcmToken]);

  const handleSubscriptionUpdate = () => {
    if (selectedFireShapeId === undefined || notificationSettingsDisabled) {
      return;
    }

    toggleSubscription(selectedFireShapeId);
  };

  return (
    <>
      <NotificationErrorSnackbar
        open={updateError}
        onClose={clearUpdateError}
        message={subscriptionUpdateErrorMessage}
      />
      <SwipeableBottomDrawer open={open} onClose={onClose}>
        <Box
          sx={{
            px: 2,
            pb: 2,
            pt: useSideSheet ? 2 : 0,
          }}
        >
          <Box
            sx={{
              alignItems: "flex-start",
              display: "flex",
              gap: 1,
              justifyContent: "space-between",
              mb: 2,
            }}
          >
            <Typography
              sx={{
                flex: 1,
                fontWeight: 700,
                fontSize: "1.25rem",
                pl: 0.5,
              }}
              variant="h6"
            >
              {fireZoneUnitNameFormatter(selectedFireShape?.mof_fire_zone_name)}
            </Typography>
            <IconButton
              aria-label="Close fire zone actions"
              data-testid="fire-shape-drawer-close-button"
              onClick={onClose}
              size="small"
            >
              <CloseIcon />
            </IconButton>
          </Box>

          <Box
            sx={{
              display: "grid",
              gap: 1.5,
              gridTemplateColumns: useSideSheet
                ? "repeat(2, minmax(0, 1fr))"
                : "repeat(3, minmax(0, 1fr))",
            }}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
              }}
            >
              <Button
                aria-label={`Toggle subscription for ${
                  selectedFireShape?.mof_fire_zone_name ?? "selected fire zone"
                }`}
                disabled={
                  selectedFireShapeId === undefined ||
                  notificationSettingsDisabled
                }
                disableElevation
                onClick={handleSubscriptionUpdate}
                sx={{ ...actionButtonSx, width: "100%" }}
                variant="text"
              >
                {isAwaitingToken ? (
                  <CircularProgress size={actionIconSize} color="inherit" />
                ) : isSubscribed ? (
                  <NotificationsActiveIcon sx={actionIconSx} />
                ) : (
                  <NotificationsNoneOutlinedIcon sx={actionIconSx} />
                )}
                {isSubscribed ? "Unsubscribe" : "Subscribe"}
              </Button>
            </Box>
            <Button
              disableElevation
              onClick={onSelectProfile}
              sx={actionButtonSx}
              variant="text"
            >
              <AnalyticsIcon sx={actionIconSx} />
              Profile
            </Button>
            <Button
              disableElevation
              onClick={onSelectAdvisory}
              sx={actionButtonSx}
              variant="text"
            >
              <TextSnippetIcon sx={actionIconSx} />
              Advisory
            </Button>
          </Box>
        </Box>
      </SwipeableBottomDrawer>
    </>
  );
};

export default FireShapeActionsDrawer;
