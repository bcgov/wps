import { MAP_BUTTON_GREY } from "@/theme";
import { IconButton, IconButtonProps, SxProps, Theme } from "@mui/material";
import React from "react";

export const BORDER_RADIUS = 8;
export const BUTTON_HEIGHT = 42;

interface MapIconButtonProps extends Omit<IconButtonProps, "sx" | "children"> {
  icon: React.ReactElement;
  sx?: SxProps<Theme>;
  testid?: string;
  loading?: boolean;
}

const MapIconButton = ({
  icon,
  sx,
  testid,
  loading,
  ...props
}: MapIconButtonProps) => {
  return (
    <IconButton
      data-testid={testid}
      size="large"
      loading={loading}
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
        "&.MuiIconButton-loading": {
          backgroundColor: "white",
        },
        ...sx,
      }}
      {...props}
    >
      {!loading && icon}
    </IconButton>
  );
};

export default MapIconButton;
