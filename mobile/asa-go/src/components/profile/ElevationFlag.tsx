import Flag from "@/components/profile/FillableFlag";
import { Grid2 as Grid } from "@mui/material";
import React from "react";

interface ElevationFlagProps {
  id: string;
  percent: number;
  testId?: string;
}

const ElevationFlag = ({ id, percent, testId }: ElevationFlagProps) => {
  return (
    <Grid
      size={6}
      sx={{ alignItems: "center", display: "flex", justifyContent: "flex-end" }}
    >
      <Flag maskId={id} percent={percent} testId={testId} />
    </Grid>
  );
};

export default React.memo(ElevationFlag);
