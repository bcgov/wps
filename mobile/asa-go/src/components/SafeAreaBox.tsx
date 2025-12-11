import { Box, BoxProps } from "@mui/material";
import { forwardRef } from "react";

/**
 * A Box component that automatically applies safe area insets.
 * Uses CSS env() to respect device notches, cameras, and rounded corners.
 */
export const SafeAreaBox = forwardRef<HTMLDivElement, BoxProps>(
  (props, ref) => {
    const { sx, ...otherProps } = props;

    return (
      <Box
        ref={ref}
        {...otherProps}
        sx={{
          paddingTop: "env(safe-area-inset-top)",
          paddingRight: "env(safe-area-inset-right)",
          paddingBottom: "env(safe-area-inset-bottom)",
          paddingLeft: "env(safe-area-inset-left)",
          ...sx,
        }}
      />
    );
  }
);

SafeAreaBox.displayName = "SafeAreaBox";
