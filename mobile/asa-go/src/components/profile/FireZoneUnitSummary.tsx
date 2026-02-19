import ElevationStatus from "@/components/profile/ElevationStatus";
import FuelSummary from "@/components/profile/FuelSummary";
import { AdvisoryTypography } from "@/components/report/AdvisoryText";
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
              stats.fire_zone_id === selectedFireZoneUnit?.fire_shape_id,
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
      <AdvisoryTypography data-testid="fire-zone-unit-summary-empty">
        {`No profile data available for the ${selectedFireCenter?.name}.`}
      </AdvisoryTypography>
    );
  }

  return (
    <Box
      data-testid="fire-zone-unit-summary"
      sx={{
        backgroundColor: "white",
        width: "100%",
        border: "1px solid #ccc",
        borderRadius: 1,
        paddingTop: theme.spacing(2),
        overflowY: "auto",
      }}
    >
      <Typography
        data-testid="fire-zone-title-tabs"
        sx={{
          color: theme.palette.primary.main,
          fontWeight: "bold",
          fontSize: "1.25rem",
          pb: theme.spacing(2),
          pl: theme.spacing(1),
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
        <Grid sx={{ px: theme.spacing(1) }}>
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
