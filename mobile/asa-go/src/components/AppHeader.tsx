import { AppBar, Box, Toolbar, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";
import { useRef, useLayoutEffect, useState } from "react";
import { theme } from "@/theme";
import { HamburgerMenu } from "@/components/HamburgerMenu";

export const AppHeader = () => {
  const headerRef = useRef<HTMLDivElement>(null);
  const [drawerTop, setDrawerTop] = useState(0);
  const [drawerHeight, setDrawerHeight] = useState(0);

  useLayoutEffect(() => {
    if (headerRef.current) {
      const headerRect = headerRef.current.getBoundingClientRect();
      setDrawerTop(headerRect.bottom);
      setDrawerHeight(window.innerHeight - headerRect.bottom);
    }
  }, []);

  return (
    <Box
      ref={headerRef}
      sx={{
        height: 100,
        background: theme.palette.primary.main,
        borderBottomWidth: 2,
        borderBottomStyle: "solid",
        borderBottomColor: theme.palette.secondary.main,
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
            <HamburgerMenu drawerTop={drawerTop} drawerHeight={drawerHeight} />
          </Toolbar>
        </AppBar>
      </Grid>
    </Box>
  );
};
