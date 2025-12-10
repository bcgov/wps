import { HamburgerMenu } from "@/components/HamburgerMenu";
import { useSafeAreaInsets } from "@/hooks/useSafeAreaInsets";
import { theme } from "@/theme";
import { AppBar, Box, Toolbar, Typography, useMediaQuery } from "@mui/material";
import Grid from "@mui/material/Grid2";
import { useLayoutEffect, useRef, useState } from "react";

export const AppHeader = () => {
  const headerRef = useRef<HTMLDivElement>(null);
  const [drawerTop, setDrawerTop] = useState(0);
  const [drawerHeight, setDrawerHeight] = useState(0);
  const isLandscape = useMediaQuery("(orientation: landscape)");
  // iPads typically have min-width of 1024px in landscape (iPad Mini+)
  // iPhones max out at ~932px in landscape, so 1024px reliably detects iPads
  const isLargeDevice = useMediaQuery("(min-width: 1024px)");
  const safePadding = useSafeAreaInsets();

  useLayoutEffect(() => {
    if (headerRef.current) {
      const headerRect = headerRef.current.getBoundingClientRect();
      setDrawerTop(headerRect.bottom);
      setDrawerHeight(window.innerHeight - headerRect.bottom);
    }
  }, []);

  // Hide header only on small devices in landscape (e.g., phones)
  // Keep header visible on large devices (e.g., iPads) even in landscape
  if (isLandscape && !isLargeDevice) {
    return null;
  }

  return (
    <Box
      ref={headerRef}
      sx={{
        height: 100,
        background: theme.palette.primary.main,
        borderBottomWidth: 2,
        borderBottomStyle: "solid",
        borderBottomColor: theme.palette.secondary.main,
        ...safePadding,
      }}
    >
      <Grid
        container
        spacing={1}
        sx={{
          width: "100%",
          marginTop: 5,
        }}
      >
        <AppBar position="static" sx={{ width: "100%" }}>
          <Toolbar sx={{ display: "flex", justifyContent: "flex-end" }}>
            <Typography variant="h6" component="div" sx={{ mr: 0.5 }}>
              ASA
            </Typography>
            <HamburgerMenu
              testId="hamburger-menu"
              drawerTop={drawerTop}
              drawerHeight={drawerHeight}
            />
          </Toolbar>
        </AppBar>
      </Grid>
    </Box>
  );
};
