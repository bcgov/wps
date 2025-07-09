import { FireShape } from "@/api/fbaAPI";
import { Close } from "@mui/icons-material";
import { Box, Button, IconButton, useTheme } from "@mui/material";
import { isUndefined } from "lodash";
import { forwardRef } from "react";

interface MapPopupProps {
  selectedFireShape: FireShape | undefined;
  onClose: () => void;
  onSelectProfile: () => void;
  onSelectReport: () => void;
  onSelectZoom: () => void;
}

const MapPopup = forwardRef(
  (
    {
      selectedFireShape,
      onClose,
      onSelectProfile,
      onSelectReport,
      onSelectZoom,
    }: MapPopupProps,
    ref
  ) => {
    const theme = useTheme();
    const formatZoneName = (name: string | undefined): string => {
      if (isUndefined(name)) {
        return "";
      }
      const index = name.toLocaleLowerCase().indexOf("zone");
      return name.slice(0, index + 4);
    };
    return (
      <Box
        ref={ref}
        sx={{
          background: "white",
          borderRadius: "8px",
          display: "flex",
          flexDirection: "column",
          minWidth: "150px",
          maxWidth: "225px",
        }}
      >
        <Box
          sx={{
            backgroundColor: theme.palette.primary.main,
            borderBottom: `1px solid ${theme.palette.secondary.main}`,
            borderTopLeftRadius: "8px",
            borderTopRightRadius: "8px",
            display: "flex",
          }}
        >
          <Box
            sx={{
              alignItems: "center",
              display: "flex",
              color: "white",
              flexGrow: 1,
              px: theme.spacing(1),
              py: theme.spacing(0.5),
            }}
          >
            {formatZoneName(selectedFireShape?.mof_fire_zone_name)}
          </Box>
          <IconButton
            data-testid="map-popup-close-button"
            onClick={onClose}
            sx={{ color: "white", padding: "2px" }}
          >
            <Close />
          </IconButton>
        </Box>
        <Button onClick={onSelectReport}>View Report</Button>
        <Button onClick={onSelectProfile}>View Profile</Button>
        <Button onClick={onSelectZoom}>Zoom to fire zone</Button>
      </Box>
    );
  }
);

export default MapPopup;
