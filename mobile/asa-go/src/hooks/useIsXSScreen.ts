import { useMediaQuery, useTheme } from "@mui/material";

export function useIsXSSmallScreen() {
  const theme = useTheme();
  const maxXSScreenDimension = theme.breakpoints.values.sm;

  // Require one dimension to be less than the threshold so the result stays
  // stable when rotating a phone into landscape.
  return useMediaQuery(
    `(max-width:${maxXSScreenDimension}px) or (max-height:${maxXSScreenDimension}px)`,
  );
}
