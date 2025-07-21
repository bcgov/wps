import Flag from "@/components/profile/FillableFlag";
import { Box, Grid2 as Grid, Typography } from "@mui/material";
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
      <Box sx={{position: "relative"}}>
        <Flag maskId={id} percent={percent} />
      </Box>

      <Typography
        sx={{
          fontSize: "1.25em",
          fontWeight: "bold",
          marginRight: "20px",
          position: "absolute",
          textShadow:
            "-2px 2px 4px #FFF, 2px 2px 4px #FFF, 2px -2px 4px #FFF, -2px -2px 4px #FFF",
        }}
        data-testid={testId}
      >
        {percent}%
      </Typography>
    </Grid>
  );
};

export default React.memo(ElevationFlag);
