import { HamburgerMenu } from "@/components/HamburgerMenu";
import { theme } from "@/theme";
import { NavPanel } from "@/utils/constants";
import {
  Analytics,
  LocalFireDepartment,
  TextSnippet,
} from "@mui/icons-material";
import { AppBar, Box, Toolbar, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";
import { useEffect, useLayoutEffect, useRef, useState } from "react";

interface AppHeaderProps {
  tab: NavPanel;
}

export const AppHeader = ({ tab }: AppHeaderProps) => {
  const headerRef = useRef<HTMLDivElement>(null);
  const [drawerTop, setDrawerTop] = useState(0);
  const [drawerHeight, setDrawerHeight] = useState(0);
  const [icon, setIcon] = useState<React.ReactNode>(<LocalFireDepartment />);
  const [title, setTitle] = useState<string>("");

  useLayoutEffect(() => {
    if (headerRef.current) {
      const headerRect = headerRef.current.getBoundingClientRect();
      setDrawerTop(headerRect.bottom);
      setDrawerHeight(window.innerHeight - headerRect.bottom);
    }
  }, []);

  useEffect(() => {
    switch (tab) {
      case NavPanel.ADVISORY:
        setIcon(<TextSnippet />);
        setTitle("Advisory Report");
        break;
      case NavPanel.PROFILE:
        setIcon(<Analytics />);
        setTitle("Profile");
        break;
      default:
        setIcon(<LocalFireDepartment />);
        setTitle("ASA Go");
        break;
    }
  }, [tab]);

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
          <Toolbar sx={{ display: "flex" }}>
            {icon}
            <Typography
              sx={{
                display: "flex",
                flexGrow: 1,
                marginLeft: theme.spacing(1),
              }}
              variant="h5"
            >
              {title}
            </Typography>
            <HamburgerMenu drawerTop={drawerTop} drawerHeight={drawerHeight} />
          </Toolbar>
        </AppBar>
      </Grid>
    </Box>
  );
};
