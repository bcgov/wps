import Flag from "@/components/profile/FillableFlag";
import { Grid2 as Grid } from "@mui/material";
import React from "react";

interface ElevationFlagProps {
  percent: number;
  testId?: string;
}

const ElevationFlag = ({ percent, testId }: ElevationFlagProps) => {
  const uniqueId = `${Date.now()}-${Math.random().toString(36)}`;

  return (
    <Grid
      size={6}
      sx={{ alignItems: "center", display: "flex", justifyContent: "flex-end" }}
    >
      <Flag
        maskId={`elevation-flag-${uniqueId}`}
        percent={percent}
        testId={testId}
      />
    </Grid>
  );
};

export default React.memo(ElevationFlag);
