import { FireCentreFireZoneUnits } from "@/api/fbaAPI";
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
  disabled: boolean;
  fireCentreFireZoneUnits: FireCentreFireZoneUnits;
}

const SubscriptionAccordion = ({
  disabled,
  fireCentreFireZoneUnits,
}: SubscriptionAccordionProps) => {
  const dispatch: AppDispatch = useDispatch();
  const { pinnedFireCentre } = useSelector(selectSettings);
  const [expanded, setExpanded] = useState(false);

  const handleChange = useCallback(
    (_: React.SyntheticEvent, newExpanded: boolean) => {
      if (disabled) return; // block expansion when disabled
      setExpanded(newExpanded);
    },
    [disabled],
  );

  const handlePinTouch = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (pinnedFireCentre === fireCentreFireZoneUnits.fire_centre_name) {
      console.log("DEBUG: Turning off pinned fire centre");
      dispatch(savePinnedFireCentre(null));
    } else {
      dispatch(savePinnedFireCentre(fireCentreFireZoneUnits.fire_centre_name));
      console.log("DEBUG: Turning on pinned fire centre");
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
            {pinnedFireCentre === fireCentreFireZoneUnits.fire_centre_name ? (
              <PushPinIcon color="primary" />
            ) : (
              <PushPinOutlinedIcon color="primary" />
            )}
          </IconButton>
          <Typography
            variant="body1"
            sx={{ fontWeight: 600, pl: theme.spacing(1) }}
          >
            {nameFormatter(
              fireCentreFireZoneUnits.fire_centre_name,
              "Fire Centre",
            )}
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            {fireCentreFireZoneUnits.fire_zone_units.map((fireZoneUnit) => {
              return (
                <SubscriptionOption
                  key={fireZoneUnit.id}
                  fireZoneUnit={fireZoneUnit.name}
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
