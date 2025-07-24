import { Box, Grid2 as Grid, Typography } from "@mui/material";
import { FireCenter, FireShape } from "api/fbaAPI";
import { isNil, isUndefined } from "lodash";
import React, { useMemo } from "react";
import FuelSummary from "@/components/profile/FuelSummary";
import { useTheme } from "@mui/material/styles";
import { useSelector } from "react-redux";
import { selectFilteredFireCentreHFIFuelStats } from "@/slices/fireCentreHFIFuelStatsSlice";
import ElevationStatus from "@/components/profile/ElevationStatus";
import { selectFireCentreTPIStats } from "@/store";
import { hasRequiredFields } from "@/utils/profileUtils";

interface FireZoneUnitSummaryProps {
  selectedFireCenter: FireCenter | undefined;
  selectedFireZoneUnit: FireShape | undefined;
}

const FireZoneUnitSummary = ({
  selectedFireCenter,
  selectedFireZoneUnit,
}: FireZoneUnitSummaryProps) => {
  const theme = useTheme();

  // selectors
  const filteredFireCentreHFIFuelStats = useSelector(
    selectFilteredFireCentreHFIFuelStats
  );
  const { fireCentreTPIStats } = useSelector(selectFireCentreTPIStats);

  // derived state
  const hfiFuelStats = useMemo(() => {
    if (selectedFireCenter) {
      return filteredFireCentreHFIFuelStats?.[selectedFireCenter?.name];
    }
  }, [filteredFireCentreHFIFuelStats, selectedFireCenter]);

  const fireZoneTPIStats = useMemo(() => {
    if (selectedFireCenter && !isNil(fireCentreTPIStats)) {
      const tpiStatsArray = fireCentreTPIStats?.firezone_tpi_stats;
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
    return <div data-testid="fire-zone-unit-summary-empty"></div>;
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
