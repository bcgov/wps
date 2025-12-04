import ElevationStatus from "@/components/profile/ElevationStatus";
import FuelSummary from "@/components/profile/FuelSummary";
import { SerifTypography } from "@/components/report/AdvisoryText";
import {
  useFilteredHFIStatsForDate,
  useTPIStatsForDate,
} from "@/hooks/dataHooks";
import { hasRequiredFields } from "@/utils/profileUtils";
import { Box, Grid2 as Grid, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { FireCenter, FireShape } from "api/fbaAPI";
import { isNil, isUndefined } from "lodash";
import { DateTime } from "luxon";
import React, { useMemo } from "react";

interface FireZoneUnitSummaryProps {
  date: DateTime;
  selectedFireCenter: FireCenter | undefined;
  selectedFireZoneUnit: FireShape | undefined;
}

const FireZoneUnitSummary = ({
  date,
  selectedFireCenter,
  selectedFireZoneUnit,
}: FireZoneUnitSummaryProps) => {
  const theme = useTheme();

  // hooks
  const filteredFireZoneUnitHFIStats = useFilteredHFIStatsForDate(date);
  const fireCentreTPIStats = useTPIStatsForDate(date);

  // derived state
  const hfiFuelStats = useMemo(() => {
    if (selectedFireCenter) {
      return filteredFireZoneUnitHFIStats;
    }
  }, [filteredFireZoneUnitHFIStats, selectedFireCenter]);

  const fireZoneTPIStats = useMemo(() => {
    if (selectedFireCenter && !isNil(fireCentreTPIStats)) {
      const tpiStatsArray = fireCentreTPIStats;
      return tpiStatsArray
        ? tpiStatsArray.find(
            (stats) =>
              stats.fire_zone_id === selectedFireZoneUnit?.fire_shape_id
          )
        : undefined;
    }
  }, [
    fireCentreTPIStats,
    selectedFireCenter,
    selectedFireZoneUnit?.fire_shape_id,
  ]);

  const fireZoneFuelStats = useMemo(() => {
    if (
      hfiFuelStats &&
      selectedFireZoneUnit &&
      hfiFuelStats[selectedFireZoneUnit.fire_shape_id]?.fuel_area_stats
    ) {
      return {
        [selectedFireZoneUnit.fire_shape_id]:
          hfiFuelStats[selectedFireZoneUnit.fire_shape_id].fuel_area_stats,
      };
    }
    return {};
  }, [hfiFuelStats, selectedFireZoneUnit]);

  if (isUndefined(selectedFireZoneUnit)) {
    return (
      <SerifTypography data-testid="fire-zone-unit-summary-empty">
        {`No profile data available for the ${selectedFireCenter?.name}.`}
      </SerifTypography>
    );
  }

  return (
    <Box
      data-testid="fire-zone-unit-summary"
      sx={{
        backgroundColor: "white",
        width: "100%",
        padding: theme.spacing(2),
        overflowY: "auto",
      }}
    >
      <Typography
        data-testid="fire-zone-title-tabs"
        sx={{
          color: "#003366",
          fontWeight: "bold",
          pb: theme.spacing(2),
        }}
      >
        {selectedFireZoneUnit.mof_fire_zone_name}
      </Typography>
      <Grid
        container
        alignItems={"center"}
        direction={"column"}
        sx={{ width: "100%" }}
      >
        <Grid sx={{ pb: theme.spacing(4), width: "100%" }}>
          <FuelSummary
            selectedFireZoneUnit={selectedFireZoneUnit}
            fireZoneFuelStats={fireZoneFuelStats}
          />
        </Grid>
        <Grid sx={{ width: "100%" }}>
          {fireZoneTPIStats && hasRequiredFields(fireZoneTPIStats) ? (
            <ElevationStatus tpiStats={fireZoneTPIStats}></ElevationStatus>
          ) : (
            <Typography>No elevation information available.</Typography>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default React.memo(FireZoneUnitSummary);
