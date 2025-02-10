import { Box } from "@mui/material";
import Grid from "@mui/material/Grid2";

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
  return (
    <Box
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
          flexGrow: 1,
          width: "fit-content",
          marginTop: 5,
          justifyContent: "space-between",
        }}
      >
        <Grid>
          <Grid>
            <HamburgerMenu
              runType={runType}
              setRunType={setRunType}
              date={date}
              updateDate={updateDate}
              fireCenterOptions={fireCenterOptions}
              setSelectedFireCenter={setSelectedFireCenter}
              setSelectedFireShape={setSelectedFireShape}
              setZoomSource={setZoomSource}
            />
          </Grid>
        </Grid>
      </Grid>
    </Box>
  );
};
