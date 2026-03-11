import { Grid2 as Grid, Typography } from "@mui/material";
import React from "react";

interface ElevationLabelProps {
  label: string;
}

const ElevationLabel = ({ label }: ElevationLabelProps) => {
  return (
    <Grid
      sx={{
        alignItems: "center",
        display: "flex",
        justifyContent: "flex-start",
      }}
      size={6}
    >
      <Typography sx={{ fontWeight: "bold", fontSize: "1.2rem" }}>
        {label}
      </Typography>
    </Grid>
  );
};

export default React.memo(ElevationLabel);
