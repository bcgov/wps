import { useMediaQuery, useTheme } from "@mui/material";

export function useIsTablet() {
  const theme = useTheme();
  const minTabletDimension = theme.breakpoints.values.md;

  // Require both dimensions to clear the tablet threshold so the result stays
  // stable when rotating a phone into landscape.
  return useMediaQuery(
    `(min-width:${minTabletDimension}px) and (min-height:${minTabletDimension}px)`,
  );
}
