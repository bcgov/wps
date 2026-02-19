import Flag from "@/components/profile/FillableFlag";
import { Grid2 as Grid, Typography } from "@mui/material";
import React from "react";

interface ElevationFlagProps {
  percent: number;
  testId?: string;
}

const ElevationFlag = ({ percent, testId }: ElevationFlagProps) => {
  const uniqueId = React.useId();

  return (
    <Grid
      size={6}
      sx={{ alignItems: "center", display: "flex", justifyContent: "flex-end" }}
    >
      <Typography
        sx={{ fontSize: "1.2rem", fontWeight: "bold", marginRight: 1 }}
        data-testid={testId}
      >
        {percent}%
      </Typography>
      <Flag
        maskId={`elevation-flag-${uniqueId}`}
        percent={percent}
        showPercent={false}
      />
    </Grid>
  );
};

export default React.memo(ElevationFlag);
