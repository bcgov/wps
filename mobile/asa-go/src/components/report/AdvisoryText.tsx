import {
  FireCenter,
  FireShape,
  FireZoneFuelStats,
  FireZoneHFIStats,
} from "@/api/fbaAPI";
import DefaultText from "@/components/report/DefaultText";
import {
  useFilteredHFIStatsForDate,
  useProvincialSummaryForDate,
} from "@/hooks/dataHooks";
import { useRunParameterForDate } from "@/hooks/useRunParameterForDate";
import { today } from "@/utils/dataSliceUtils";
import {
  getTopFuelsByArea,
  getTopFuelsByProportion,
  getZoneMinWindStatsText,
} from "@/utils/advisoryTextUtils";
import { calculateStatusText } from "@/utils/calculateZoneStatus";
import { AdvisoryStatus } from "@/utils/constants";
import {
  criticalHoursExtendToNextDay,
  formatCriticalHoursTimeText,
  getMinStartAndMaxEndTime,
} from "@/utils/criticalHoursStartEndTime";
import { Box, styled, Typography, useTheme } from "@mui/material";
import { isEmpty, isNil, isUndefined } from "lodash";
import { DateTime } from "luxon";
import { useMemo } from "react";

export const SerifTypography = styled(Typography)({
  fontSize: "1.2rem",
  fontFamily: '"Courier", "Monospace"',
}) as typeof Typography;

interface AdvisoryTextProps {
  advisoryThreshold: number;
  selectedFireCenter: FireCenter | undefined;
  selectedFireZoneUnit: FireShape | undefined;
  date: DateTime;
}

const AdvisoryText = ({
  advisoryThreshold,
  selectedFireCenter,
  selectedFireZoneUnit,
  date,
}: AdvisoryTextProps) => {
  const theme = useTheme();

  // hooks
  const provincialSummary = useProvincialSummaryForDate(date);
  const filteredFireZoneUnitHFIStats = useFilteredHFIStatsForDate(date);
  const runParameter = useRunParameterForDate(date);

  // derived state
  const selectedFilteredZoneUnitFuelStats = useMemo<FireZoneHFIStats>(() => {
    if (
      isUndefined(filteredFireZoneUnitHFIStats) ||
      isEmpty(filteredFireZoneUnitHFIStats) ||
      isUndefined(selectedFireZoneUnit) ||
      isNil(runParameter)
    ) {
      return { fuel_area_stats: [], min_wind_stats: [] };
    }
    return (
      filteredFireZoneUnitHFIStats?.[selectedFireZoneUnit.fire_shape_id] ?? {
        fuel_area_stats: [],
        min_wind_stats: [],
      }
    );
  }, [filteredFireZoneUnitHFIStats, selectedFireZoneUnit]);

  const selectedFireZoneUnitTopFuels = useMemo<FireZoneFuelStats[]>(() => {
    if (isNil(runParameter?.for_date)) {
      return [];
    }
    return getTopFuelsByArea(
      selectedFilteredZoneUnitFuelStats,
      DateTime.fromISO(runParameter.for_date)
    );
  }, [selectedFilteredZoneUnitFuelStats, runParameter]);

  const highHFIFuelsByProportion = useMemo<FireZoneFuelStats[]>(() => {
    return getTopFuelsByProportion(
      selectedFilteredZoneUnitFuelStats.fuel_area_stats
    );
  }, [selectedFilteredZoneUnitFuelStats]);

  const {
    minStartTime,
    maxEndTime,
    duration: criticalHoursDuration,
  } = useMemo(() => {
    return getMinStartAndMaxEndTime(selectedFireZoneUnitTopFuels);
  }, [selectedFireZoneUnitTopFuels]);

  const zoneStatus = useMemo(() => {
    if (selectedFireCenter) {
      const fireCenterSummary = provincialSummary?.[selectedFireCenter.name];
      const fireZoneUnitInfos = fireCenterSummary?.filter(
        (fc) => fc.fire_shape_id === selectedFireZoneUnit?.fire_shape_id
      );
      const zoneStatus = calculateStatusText(
        fireZoneUnitInfos,
        advisoryThreshold
      );
      return zoneStatus;
    }
  }, [
    advisoryThreshold,
    selectedFireCenter,
    selectedFireZoneUnit,
    provincialSummary,
  ]);

  const getCommaSeparatedString = (array: string[]): string => {
    // Slice off the last two items and join then with ' and ' to create a new string. Then take the first n-2 items and
    // deconstruct them into a new array along with the new string. Finally, join the items in the new array with ', '.
    const joinedFuelTypes = [
      ...array.slice(0, -2),
      array.slice(-2).join(" and "),
    ].join(", ");
    return joinedFuelTypes;
  };

  const getTopFuelsString = () => {
    const topFuelCodes = [
      ...new Set(
        selectedFireZoneUnitTopFuels.map(
          (topFuel) => topFuel.fuel_type.fuel_type_code
        )
      ),
    ];
    const lowercaseZoneStatus = zoneStatus?.toLowerCase();
    switch (topFuelCodes.length) {
      case 0:
        return "";
      case 1:
        return `${topFuelCodes[0]} is the most prevalent fuel type under ${lowercaseZoneStatus}.`;
      case 2:
        return `${topFuelCodes[0]} and ${topFuelCodes[1]} are the most prevalent fuel types under ${lowercaseZoneStatus}.`;
      default:
        return `${getCommaSeparatedString(
          topFuelCodes
        )} are the most prevalent fuel types under ${lowercaseZoneStatus}.`;
    }
  };

  const getHighProportionFuelsString = (): string => {
    const topFuelCodes = new Set(
      selectedFireZoneUnitTopFuels.map(
        (topFuel) => topFuel.fuel_type.fuel_type_code
      )
    );

    const highProportionFuels = [
      ...new Set(
        highHFIFuelsByProportion
          .filter((fuel) => !topFuelCodes.has(fuel.fuel_type.fuel_type_code))
          .map((fuel_type) => fuel_type.fuel_type.fuel_type_code)
      ),
    ];
    switch (highProportionFuels.length) {
      case 0:
        return "";
      case 1:
        return `${highProportionFuels[0]} occupies a small portion of the zone but is expected to challenge suppression wherever it occurs.\n\n`;
      case 2:
        return `${highProportionFuels[0]} and ${highProportionFuels[1]} occupy a small portion of the zone but are expected to challenge suppression wherever they occur.\n\n`;
      default:
        return `${getCommaSeparatedString(
          highProportionFuels
        )} occupy a small portion of the zone but are expected to challenge suppression wherever they occur.\n\n`;
    }
  };

  const getAdditionalDetailText = (
    minStartTime?: number,
    maxEndTime?: number
  ): React.ReactNode => {
    const isEarlyAdvisory = minStartTime !== undefined && minStartTime < 12;
    const isOvernightBurnPossible =
      minStartTime !== undefined &&
      maxEndTime !== undefined &&
      (maxEndTime > 23 ||
        criticalHoursExtendToNextDay(minStartTime, maxEndTime));
    const showSlashMessage =
      !isUndefined(criticalHoursDuration) && criticalHoursDuration > 12;
    return (
      <>
        {isEarlyAdvisory && (
          <SerifTypography component="span" data-testid="early-advisory-text">
            Be prepared for fire behaviour to increase early in the day
            {!isOvernightBurnPossible && "."}
          </SerifTypography>
        )}
        {isEarlyAdvisory && isOvernightBurnPossible && " "}
        {isOvernightBurnPossible && (
          <SerifTypography
            component="span"
            data-testid="overnight-burning-text"
          >
            {isEarlyAdvisory
              ? "and remain elevated into the overnight hours."
              : "Be prepared for fire behaviour to remain elevated into the overnight hours."}
          </SerifTypography>
        )}
        {(isEarlyAdvisory || isOvernightBurnPossible) && " "}
        {showSlashMessage && (
          <SerifTypography
            component="span"
            data-testid="advisory-message-slash"
          >
            {
              "Slash fuel types will exhibit high fire intensity throughout the burning period."
            }
          </SerifTypography>
        )}
      </>
    );
  };

  const renderDefaultMessage = () => {
    return (
      <>
        {isNil(selectedFireCenter) ? (
          <DefaultText />
        ) : (
          <SerifTypography data-testid="no-data-message">
            No advisory data available for the selected date.
          </SerifTypography>
        )}
      </>
    );
  };

  const renderAdvisoryText = () => {
    const zoneTitle = `${selectedFireZoneUnit?.mof_fire_zone_name}:\n\n`;
    const forToday = runParameter?.for_date === today.toISODate();
    const displayForDate = forToday
      ? "today"
      : DateTime.fromISO(runParameter!.for_date).toLocaleString({
          month: "short",
          day: "numeric",
        });
    const minWindSpeedText = getZoneMinWindStatsText(
      selectedFilteredZoneUnitFuelStats.min_wind_stats
    );

    const formattedWindText = minWindSpeedText ? (
      <SerifTypography
        component="span"
        data-testid="advisory-message-wind-speed"
      >
        {" "}
        {minWindSpeedText}
      </SerifTypography>
    ) : null;

    const hasCriticalHours = !isNil(minStartTime) && !isNil(maxEndTime);
    let message: React.ReactNode = null;
    if (hasCriticalHours) {
      const [formattedStartTime, formattedEndTime] =
        formatCriticalHoursTimeText(minStartTime, maxEndTime, false);
      message = (
        <>
          There is a fire behaviour {zoneStatus?.toLowerCase()} in effect for{" "}
          {selectedFireZoneUnit?.mof_fire_zone_name} between{" "}
          {formattedStartTime} and {formattedEndTime}
          {formattedWindText}. {getTopFuelsString()}
          <br />
          <br />
        </>
      );
    } else {
      message = (
        <>
          There is a fire behaviour {zoneStatus?.toLowerCase()} in effect for{" "}
          {selectedFireZoneUnit?.mof_fire_zone_name}
          {formattedWindText}. {getTopFuelsString()}
          <br />
          <br />
        </>
      );
    }

    const earlyOvernightBurning = getAdditionalDetailText(
      minStartTime,
      maxEndTime
    );

    return (
      <>
        {selectedFireZoneUnit && (
          <SerifTypography
            data-testid="fire-zone-unit-bulletin"
            sx={{ whiteSpace: "pre-wrap" }}
          >
            {zoneTitle}
          </SerifTypography>
        )}

        {runParameter?.run_datetime && (
          <SerifTypography
            data-testid="bulletin-issue-date"
            sx={{ whiteSpace: "pre-wrap" }}
          >
            {`Issued on ${DateTime.fromISO(
              runParameter.run_datetime
            )?.toLocaleString(
              DateTime.DATETIME_FULL
            )} for ${displayForDate}.\n\n`}
          </SerifTypography>
        )}

        {!isUndefined(zoneStatus) ? (
          <>
            {zoneStatus === AdvisoryStatus.ADVISORY && (
              <SerifTypography
                sx={{ whiteSpace: "pre-line" }}
                data-testid="advisory-message-advisory"
              >
                {message}
              </SerifTypography>
            )}

            {zoneStatus === AdvisoryStatus.WARNING && (
              <SerifTypography
                sx={{ whiteSpace: "pre-line" }}
                data-testid="advisory-message-warning"
              >
                {message}
              </SerifTypography>
            )}

            <SerifTypography
              sx={{ whiteSpace: "pre-line" }}
              data-testid="advisory-message-proportion"
            >
              {getHighProportionFuelsString()}
            </SerifTypography>

            {earlyOvernightBurning && <>{earlyOvernightBurning}</>}

            {!hasCriticalHours && (
              <SerifTypography data-testid="advisory-message-no-critical-hours">
                No critical hours available.
              </SerifTypography>
            )}
          </>
        ) : (
          <SerifTypography data-testid="no-advisory-message">
            No advisories or warnings issued for the selected fire zone unit.
          </SerifTypography>
        )}
      </>
    );
  };

  return (
    <Box
      data-testid="advisory-text"
      sx={{
        maxWidth: "100%",
        minWidth: "100%",
        overflow: "auto",
        border: "1px solid #ccc",
        padding: theme.spacing(2),
        borderRadius: 1,
        backgroundColor: "white",
      }}
    >
      {!selectedFireCenter ||
      isNil(runParameter?.run_datetime) ||
      !selectedFireZoneUnit
        ? renderDefaultMessage()
        : renderAdvisoryText()}
    </Box>
  );
};

export default AdvisoryText;
