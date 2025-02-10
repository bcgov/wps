import { Drawer, IconButton, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";

import { Menu as MenuIcon, Close as CloseIcon } from "@mui/icons-material";

import { useState } from "react";
import { RunType, FireCenter, FireShape } from "@/api/fbaAPI";
import { DateTime } from "luxon";
import ActualForecastControl from "@/components/ActualForecastControl";
import WPSDatePicker from "@/components/WPSDatePicker";
import FireCenterDropdown from "@/components/FireCenterDropdown";
import { theme } from "@/theme";

export interface HamburgerMenuProps {
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

export const HamburgerMenu = ({
  runType,
  setRunType,
  date,
  updateDate,
  selectedFireCenter,
  fireCenterOptions,
  setSelectedFireShape,
  setSelectedFireCenter,
  setZoomSource,
}: HamburgerMenuProps) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <IconButton onClick={() => setOpen(true)}>
        <MenuIcon fontSize="large" sx={{ color: "white" }} />
      </IconButton>
      <Drawer anchor="left" open={open} onClose={() => setOpen(false)}>
        <div style={{ width: 250, padding: "16px" }}>
          {/* Close Button */}
          <IconButton onClick={() => setOpen(false)} sx={{ marginBottom: 2 }}>
            <CloseIcon />
          </IconButton>
        </div>
        <Grid container spacing={1} direction={"column"} sx={{}}>
          <Grid>
            <Typography
              variant="h2"
              sx={{
                color: theme.palette.primary.contrastText,
                fontSize: "1.7rem",
              }}
            >
              ASA
            </Typography>
            <Grid>
              <ActualForecastControl
                runType={runType}
                setRunType={setRunType}
              />
            </Grid>
            <Grid>
              <WPSDatePicker date={date} updateDate={updateDate} />
            </Grid>
            <Grid>
              <FireCenterDropdown
                fireCenterOptions={fireCenterOptions}
                selectedFireCenter={selectedFireCenter}
                setSelectedFireCenter={setSelectedFireCenter}
                setSelectedFireShape={setSelectedFireShape}
                setZoomSource={setZoomSource}
              />
            </Grid>
          </Grid>
        </Grid>
      </Drawer>
    </>
  );
};
