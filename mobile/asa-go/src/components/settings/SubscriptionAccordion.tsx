import { FireCentreInfo } from "@/api/fbaAPI";
import SubscriptionOption from "@/components/settings/SubscriptionOption";
import { useNotificationSettings } from "@/hooks/useNotificationSettings";
import { savePinnedFireCentre } from "@/slices/settingsSlice";
import {
  AppDispatch,
  selectNotificationSettingsDisabled,
  selectSettings,
} from "@/store";
import { theme } from "@/theme";
import { subscriptionUpdateErrorMessage } from "@/utils/constants";
import { nameFormatter } from "@/utils/stringUtils";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import PushPinIcon from "@mui/icons-material/PushPin";
import PushPinOutlinedIcon from "@mui/icons-material/PushPinOutlined";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Checkbox,
  FormControlLabel,
  FormGroup,
  IconButton,
  List,
  Typography,
} from "@mui/material";
import NotificationErrorSnackbar from "@/components/NotificationErrorSnackbar";
import { useCallback, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

interface SubscriptionAccordionProps {
  defaultExpanded: boolean;
  disabled: boolean;
  fireCentreInfo: FireCentreInfo;
}

const SubscriptionAccordion = ({
  defaultExpanded,
  disabled,
  fireCentreInfo,
}: SubscriptionAccordionProps) => {
  const dispatch: AppDispatch = useDispatch();
  const {
    updateSubscriptions,
    toggleSubscription,
    updateError,
    clearUpdateError,
  } = useNotificationSettings();
  const { pinnedFireCentre, subscriptions } = useSelector(selectSettings);
  const notificationSettingsDisabled = useSelector(
    selectNotificationSettingsDisabled,
  );

  const [expanded, setExpanded] = useState(defaultExpanded);
  const [pendingZoneId, setPendingZoneId] = useState<number | null>(null);

  // All fire zone unit ids in this fire centre.
  const allFireZoneUnitIds = useMemo(() => {
    if (fireCentreInfo?.fire_zone_units?.length) {
      return fireCentreInfo.fire_zone_units.map((fzu) => fzu.id);
    }
    return [];
  }, [fireCentreInfo]);

  // All fire zone units ids in this fire centre that are subscribed to.
  const subscribedFireZoneUnits = useMemo(() => {
    return allFireZoneUnitIds.filter((zone) => subscriptions.includes(zone));
  }, [subscriptions, allFireZoneUnitIds]);

  // Handle expanding/collapsing the accordion.
  const handleChange = useCallback(
    (_: React.SyntheticEvent, newExpanded: boolean) => {
      if (disabled) {
        return; // block expansion when disabled
      }
      setExpanded(newExpanded);
    },
    [disabled],
  );

  // Handle a touch of the pin icon to move a fire centre to the top of the group of accordions.
  const handlePinTouch = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (pinnedFireCentre === fireCentreInfo.fire_centre_name) {
      dispatch(savePinnedFireCentre(null));
    } else {
      dispatch(savePinnedFireCentre(fireCentreInfo.fire_centre_name));
    }
  };

  const allSelected = () => {
    if (
      subscribedFireZoneUnits.length &&
      subscribedFireZoneUnits.length === allFireZoneUnitIds.length
    ) {
      return true;
    }
    return false;
  };

  // Add/remove subscription to all fire zone units in this fire centre.
  const handleToggle = async (id: number) => {
    setPendingZoneId(id);
    await toggleSubscription(id);
    setPendingZoneId(null);
  };

  const toggleAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation();
    // Remove all of this fire centre's fire zone unit ids to avoid adding duplicates in the following if block.
    const newSubs = subscriptions.filter(
      (sub) => !allFireZoneUnitIds.includes(sub),
    );
    // If none or some ids are already subscribed to, add back all ids to select all.
    if (!allSelected()) {
      newSubs.push(...allFireZoneUnitIds);
    }

    updateSubscriptions(newSubs);
  };

  const disabledStyles = disabled
    ? {
        opacity: 0.5,
        filter: "grayscale(1)",
        pointerEvents: "none" as const, // block all pointer events
      }
    : {};

  return (
    <Box
      sx={{
        position: "relative",
        "& [role='button']": disabled ? { pointerEvents: "none" } : undefined,
      }}
      aria-disabled={disabled ? true : undefined}
    >
      <NotificationErrorSnackbar
        open={updateError}
        onClose={clearUpdateError}
        message={subscriptionUpdateErrorMessage}
      />
      <Accordion
        aria-label={`accordion-${fireCentreInfo.fire_centre_name}`}
        defaultExpanded={defaultExpanded}
        disabled={notificationSettingsDisabled}
        disableGutters
        expanded={expanded}
        onChange={handleChange}
        sx={{ ...disabledStyles }}
      >
        <AccordionSummary
          aria-controls={`region-${fireCentreInfo.fire_centre_name}`}
          id={`summary-${fireCentreInfo.fire_centre_name}`}
          expandIcon={<ExpandMoreIcon />}
          sx={{
            backgroundColor: "rgba(252, 186, 25, 0.30)",
          }}
        >
          <IconButton onClick={handlePinTouch}>
            {pinnedFireCentre === fireCentreInfo.fire_centre_name ? (
              <PushPinIcon color="primary" />
            ) : (
              <PushPinOutlinedIcon color="primary" />
            )}
          </IconButton>
          <Box sx={{ display: "flex", alignItems: "center", flex: 1 }}>
            <Typography
              variant="body2"
              sx={{
                display: "flex",
                flex: 1,
                flexShrink: 0,
                fontWeight: "bold",
                pl: theme.spacing(1),
              }}
            >
              {nameFormatter(
                fireCentreInfo.fire_centre_name,
                "Fire Centre",
                true,
              )}
            </Typography>
            <FormGroup>
              <FormControlLabel
                control={
                  <Checkbox
                    disabled={disabled}
                    aria-label={`checkbox-${fireCentreInfo.fire_centre_name}`}
                    checked={allSelected()}
                    indeterminate={
                      !allSelected() && subscribedFireZoneUnits.length > 0
                    }
                    onChange={toggleAll}
                    onClick={(e) => e.stopPropagation()}
                  />
                }
                label="All"
                onClick={(e) => e.stopPropagation()}
              />
            </FormGroup>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <List data-testid="switch-options">
            {fireCentreInfo.fire_zone_units.map((fireZoneUnit) => {
              return (
                <SubscriptionOption
                  key={fireZoneUnit.id}
                  fireZoneUnit={fireZoneUnit}
                  onToggle={handleToggle}
                  disabled={notificationSettingsDisabled}
                  loading={pendingZoneId === fireZoneUnit.id}
                />
              );
            })}
          </List>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default SubscriptionAccordion;
