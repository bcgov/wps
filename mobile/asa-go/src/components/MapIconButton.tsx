import { MAP_BUTTON_GREY } from "@/theme";
import { IconButton, IconButtonProps, SxProps, Theme } from "@mui/material";
import React from "react";

export const BORDER_RADIUS = 8;
export const BUTTON_HEIGHT = 42;

interface MapIconButtonProps extends Omit<IconButtonProps, "sx"> {
  icon: React.ReactElement;
  position?: {
    top?: number | string;
    right?: number | string;
    bottom?: number | string;
    left?: number | string;
  };
  sx?: SxProps<Theme>;
}

const MapIconButton: React.FC<MapIconButtonProps> = ({
  icon,
  sx,
  ...props
}) => {
  return (
    <IconButton
      size="large"
      sx={{
        backgroundColor: "white",
        color: MAP_BUTTON_GREY,
        width: BUTTON_HEIGHT,
        height: BUTTON_HEIGHT,
        borderRadius: `${BORDER_RADIUS}px`,
        "&:disabled": {
          backgroundColor: "grey.200",
        },
        ...sx,
      }}
      {...props}
    >
      {icon}
    </IconButton>
  );
};

export default MapIconButton;
