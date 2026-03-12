import { FireCentreInfo } from "@/api/fbaAPI";
import SubscriptionOption from "@/components/settings/SubscriptionOption";
import { savePinnedFireCentre } from "@/slices/settingsSlice";
import { AppDispatch, selectSettings } from "@/store";
import { theme } from "@/theme";
import { nameFormatter } from "@/utils/stringUtils";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import PushPinIcon from "@mui/icons-material/PushPin";
import PushPinOutlinedIcon from "@mui/icons-material/PushPinOutlined";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  IconButton,
  List,
  Typography,
} from "@mui/material";
import { useCallback, useState } from "react";
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
  const { pinnedFireCentre } = useSelector(selectSettings);
  const [expanded, setExpanded] = useState(defaultExpanded);

  const handleChange = useCallback(
    (_: React.SyntheticEvent, newExpanded: boolean) => {
      if (disabled) return; // block expansion when disabled
      setExpanded(newExpanded);
    },
    [disabled],
  );

  const handlePinTouch = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (pinnedFireCentre === fireCentreInfo.fire_centre_name) {
      dispatch(savePinnedFireCentre(null));
    } else {
      dispatch(savePinnedFireCentre(fireCentreInfo.fire_centre_name));
    }
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
        // Keep keyboard focus out and indicate disabled to AT
        "& [role='button']": disabled ? { pointerEvents: "none" } : undefined,
      }}
      aria-disabled={disabled ? true : undefined}
    >
      <Accordion
        defaultExpanded={defaultExpanded}
        disableGutters
        expanded={expanded}
        onChange={handleChange}
        sx={{ ...disabledStyles }}
      >
        <AccordionSummary
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
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <Typography
              variant="body2"
              sx={{ fontWeight: "bold", pl: theme.spacing(1) }}
            >
              {nameFormatter(
                fireCentreInfo.fire_centre_name,
                "Fire Centre",
                true,
              )}
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            {fireCentreInfo.fire_zone_units.map((fireZoneUnit) => {
              return (
                <SubscriptionOption
                  key={fireZoneUnit.id}
                  fireZoneUnit={fireZoneUnit}
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
