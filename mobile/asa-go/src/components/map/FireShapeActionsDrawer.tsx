import { FireShape } from "@/api/fbaAPI";
import { SwipeableBottomDrawer } from "@/components/SwipeableBottomDrawer";
import {
  checkPushNotificationPermission,
  toggleSubscription,
} from "@/slices/settingsSlice";
import { AppDispatch, selectNetworkStatus, selectSettings } from "@/store";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import CloseIcon from "@mui/icons-material/Close";
import NotificationsActiveIcon from "@mui/icons-material/NotificationsActive";
import NotificationsNoneOutlinedIcon from "@mui/icons-material/NotificationsNoneOutlined";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import { Box, Button, IconButton, Theme, Typography } from "@mui/material";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";

interface FireShapeActionsDrawerProps {
  open: boolean;
  selectedFireShape: FireShape | undefined;
  onClose: () => void;
  onSelectProfile: () => void;
  onSelectAdvisory: () => void;
}

const actionButtonSx = (theme: Theme) => ({
  borderRadius: 2,
  flexDirection: "column",
  fontSize: "1rem",
  gap: 0.75,
  minHeight: 80,
  px: 1,
  py: 1.25,
  textTransform: "none",
  [theme.breakpoints.up("sm")]: {
    fontSize: "1.25rem",
    gap: 1,
    minHeight: 88,
    py: 1.5,
  },
  [theme.breakpoints.up("md")]: {
    fontSize: "1.5rem",
    minHeight: 96,
  },
});

const actionIconSx = (theme: Theme) => ({
  fontSize: 36,
  [theme.breakpoints.up("sm")]: {
    fontSize: 40,
  },
  [theme.breakpoints.up("md")]: {
    fontSize: 44,
  },
});

const FireShapeActionsDrawer = ({
  open,
  selectedFireShape,
  onClose,
  onSelectProfile,
  onSelectAdvisory,
}: FireShapeActionsDrawerProps) => {
  const dispatch: AppDispatch = useDispatch();
  const { networkStatus } = useSelector(selectNetworkStatus);
  const { pushNotificationPermission, subscriptions } =
    useSelector(selectSettings);
  const selectedFireShapeId = selectedFireShape?.fire_shape_id;
  const isSubscribed =
    selectedFireShapeId !== undefined &&
    subscriptions.includes(selectedFireShapeId);
  const notificationSettingsDisabled =
    pushNotificationPermission !== "granted" || !networkStatus.connected;

  useEffect(() => {
    if (open && pushNotificationPermission === "unknown") {
      dispatch(checkPushNotificationPermission());
    }
  }, [dispatch, open, pushNotificationPermission]);

  const handleSubscriptionUpdate = () => {
    if (selectedFireShapeId === undefined || notificationSettingsDisabled) {
      return;
    }

    dispatch(toggleSubscription(selectedFireShapeId));
  };

  return (
    <SwipeableBottomDrawer
      open={open}
      onClose={onClose}
      ModalProps={{ keepMounted: true }}
    >
      <Box sx={{ px: 2, pb: 2 }}>
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
            sx={{ flex: 1, fontWeight: 700, fontSize: "20px" }}
            variant="h6"
          >
            {selectedFireShape?.mof_fire_zone_name ?? ""}
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
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
          }}
        >
          <Button
            aria-label={`Toggle subscription for ${
              selectedFireShape?.mof_fire_zone_name ?? "selected fire zone"
            }`}
            color={isSubscribed ? "primary" : "inherit"}
            disabled={
              selectedFireShapeId === undefined || notificationSettingsDisabled
            }
            disableElevation
            onClick={handleSubscriptionUpdate}
            sx={actionButtonSx}
            variant="text"
          >
            {isSubscribed ? (
              <NotificationsActiveIcon sx={actionIconSx} />
            ) : (
              <NotificationsNoneOutlinedIcon sx={actionIconSx} />
            )}
            {isSubscribed ? "Subscribed" : "Subscribe"}
          </Button>
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
  );
};

export default FireShapeActionsDrawer;
