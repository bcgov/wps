import { AppBar, Box, Toolbar, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";
import { useRef, useLayoutEffect, useState } from "react";

import { theme } from "@/theme";
import { HamburgerMenu } from "@/components/HamburgerMenu";
import { RunType, FireCenter, FireShape } from "@/api/fbaAPI";
import { DateTime } from "luxon";

export interface AppHeaderProps {
  runType: RunType;
  setRunType: React.Dispatch<React.SetStateAction<RunType>>;
  date: DateTime;
  updateDate: (d: DateTime) => void;
  selectedFireCenter?: FireCenter;
  fireCenterOptions: FireCenter[];
  setSelectedFireCenter: React.Dispatch<
    React.SetStateAction<FireCenter | undefined>
  >;
  setSelectedFireShape: React.Dispatch<
    React.SetStateAction<FireShape | undefined>
  >;
  setZoomSource: React.Dispatch<
    React.SetStateAction<"fireCenter" | "fireShape" | undefined>
  >;
}
export const AppHeader = ({
  runType,
  setRunType,
  date,
  updateDate,
  fireCenterOptions,
  setSelectedFireShape,
  setSelectedFireCenter,
  setZoomSource,
}: AppHeaderProps) => {
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
            <HamburgerMenu
              runType={runType}
              setRunType={setRunType}
              date={date}
              updateDate={updateDate}
              fireCenterOptions={fireCenterOptions}
              setSelectedFireCenter={setSelectedFireCenter}
              setSelectedFireShape={setSelectedFireShape}
              setZoomSource={setZoomSource}
              drawerTop={drawerTop}
              drawerHeight={drawerHeight}
            />
          </Toolbar>
        </AppBar>
      </Grid>
    </Box>
  );
};
