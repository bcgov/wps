import { Box, Typography, useTheme } from "@mui/material";
import React from "react";
import { getColorByFuelTypeCode } from "@/components/profile/color";

interface FuelDistributionProps {
  code: string;
  percent: number;
}

// Represents the percent contribution of the given fuel type to the overall high HFI area.
const FuelDistribution = ({ code, percent }: FuelDistributionProps) => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        display: "flex",
        flexGrow: 1,
        height: "100%",
        alignItems: "center",
        width: "100%",
      }}
    >
      <Box sx={{ width: "4ch", flexShrink: 0, mr: theme.spacing(1) }}>
        <Typography
          fontWeight="bold"
          sx={{
            fontSize: "0.75rem",
            textAlign: "right",
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {`${percent.toFixed(0)}%`}
        </Typography>
      </Box>
      <Box
        sx={{
          flexGrow: 1,
          height: "85%",
          display: "flex",
          alignItems: "center",
        }}
      >
        <Box
          data-testid="fuel-distribution-box"
          sx={{
            height: "100%",
            width: `${percent}%`,
            background: getColorByFuelTypeCode(code),
          }}
        ></Box>
      </Box>
    </Box>
  );
};

export default React.memo(FuelDistribution);
