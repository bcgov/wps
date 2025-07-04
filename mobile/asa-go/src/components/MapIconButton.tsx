import { MAP_BUTTON_GREY } from "@/theme";
import { IconButton, IconButtonProps, SxProps, Theme } from "@mui/material";
import React from "react";

export const BORDER_RADIUS = 8;
export const BUTTON_HEIGHT = 42;

interface MapIconButtonProps extends Omit<IconButtonProps, "sx"> {
  icon: React.ReactElement;
  sx?: SxProps<Theme>;
  testid?: string;
}

const MapIconButton: React.FC<MapIconButtonProps> = ({
  icon,
  sx,
  testid,
  ...props
}) => {
  return (
    <IconButton
      data-testid={testid}
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
        "&:hover, &:focus, &:focus-visible, &:active": {
          backgroundColor: "white",
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
