import ElevationStatus from "@/components/profile/ElevationStatus";
import FuelSummary from "@/components/profile/FuelSummary";
import { AdvisoryTypography } from "@/components/report/AdvisoryText";
import DefaultText from "@/components/report/DefaultText";
import {
  useFilteredHFIStatsForDate,
  useTPIStatsForDate,
} from "@/hooks/dataHooks";
import { hasRequiredFields } from "@/utils/profileUtils";
import { Box, Stack, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { FireShape } from "api/fbaAPI";
import type { FireCentre } from "@/types/fireCentre";
import { isNil } from "lodash";
import { DateTime } from "luxon";
import React, { useMemo } from "react";

interface FireZoneUnitSummaryProps {
  date: DateTime;
  selectedFireCentre: FireCentre | undefined;
  selectedFireZoneUnit: FireShape | undefined;
}

const FireZoneUnitSummary = ({
  date,
  selectedFireCentre,
  selectedFireZoneUnit,
}: FireZoneUnitSummaryProps) => {
  const theme = useTheme();

  // hooks
  const filteredFireZoneUnitHFIStats = useFilteredHFIStatsForDate(date);
  const fireCentreTPIStats = useTPIStatsForDate(date);

  // derived state
  const hfiFuelStats = useMemo(() => {
    if (selectedFireCentre) {
      return filteredFireZoneUnitHFIStats;
    }
  }, [filteredFireZoneUnitHFIStats, selectedFireCentre]);

  const fireZoneTPIStats = useMemo(() => {
    if (selectedFireCentre && !isNil(fireCentreTPIStats)) {
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
    selectedFireCentre,
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

  const renderDefaultMessage = () => (
    <Box sx={{ px: theme.spacing(2), pb: theme.spacing(2) }}>
      {isNil(selectedFireCentre) ? (
        <DefaultText />
      ) : (
        <AdvisoryTypography data-testid="fire-zone-unit-summary-empty">
          {`No profile data available for the ${selectedFireCentre.name}.`}
        </AdvisoryTypography>
      )}
    </Box>
  );

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
      {isNil(selectedFireCentre) || isNil(selectedFireZoneUnit) ? (
        renderDefaultMessage()
      ) : (
        <>
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
          <Stack
            sx={{
              alignItems: "center",
              width: "100%",
            }}
          >
            <Box sx={{ pb: theme.spacing(4), width: "100%" }}>
              <FuelSummary
                selectedFireZoneUnit={selectedFireZoneUnit}
                fireZoneFuelStats={fireZoneFuelStats}
              />
            </Box>
            <Box sx={{ width: "100%" }}>
              {fireZoneTPIStats && hasRequiredFields(fireZoneTPIStats) ? (
                <ElevationStatus tpiStats={fireZoneTPIStats}></ElevationStatus>
              ) : (
                <Typography>No elevation information available.</Typography>
              )}
            </Box>
          </Stack>
        </>
      )}
    </Box>
  );
};

export default React.memo(FireZoneUnitSummary);
