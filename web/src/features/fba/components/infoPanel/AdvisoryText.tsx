import { Box, styled, Typography } from '@mui/material'
import { DateTime } from 'luxon'
import React, { useMemo } from 'react'
import { useSelector } from 'react-redux'
import { selectProvincialSummary } from 'features/fba/slices/provincialSummarySlice'
import { calculateStatusText, calculateWindSpeedText } from '@/features/fba/calculateZoneStatus'
import {
  criticalHoursExtendToNextDay,
  formatCriticalHoursTimeText,
  getMinStartAndMaxEndTime
} from '@/features/fba/criticalHoursStartEndTime'
import { AdvisoryMinWindStats, FireCenter, FireShape, FireZoneFuelStats, FireZoneHFIStats } from 'api/fbaAPI'
import { groupBy, isEmpty, isNil, isUndefined } from 'lodash'
import { AdvisoryStatus } from 'utils/constants'
import { selectFilteredFireCentreHFIFuelStats } from '@/app/rootReducer'

const SLASH_FUEL_TYPES = ['S-1', 'S-2', 'S-3']

// Return a list of fuel stats for which greater than 90% of the area of each fuel type has high HFI.
export const getTopFuelsByProportion = (zoneUnitFuelStats: FireZoneFuelStats[]): FireZoneFuelStats[] => {
  const groupedByFuelType = groupBy(zoneUnitFuelStats, stat => stat.fuel_type.fuel_type_code)
  const topFuelsByProportion: FireZoneFuelStats[] = []

  Object.values(groupedByFuelType).forEach(entries => {
    const totalArea = entries.reduce((sum, entry) => sum + entry.area, 0)
    const fuelArea = entries[0].fuel_area
    if (totalArea / fuelArea >= 0.9) {
      topFuelsByProportion.push(...entries)
    }
  })
  return topFuelsByProportion
}

/**
 * Determine if we are in the core season ie between June 1 - September 30. Alternate logic for
 * handling slash fuel types in the advisory text is required during this period.
 * @param date
 * @returns True if the date is between June 1 - September 30, otherwise False.
 */
const isCoreSeason = (date: DateTime) => {
  return date.month > 5 && date.month < 10
}

/**
 * Returns the fuel type stat records that cumulatively account for more than 75% of total area with high HFI.
 * The zoneUnitFuelStats may contain more than 1 record for each fuel type, if there are pixels matching both
 * HFI class 5 and 6 for that fuel type. From June 1 - September 30 slash fuel types (S-1, S-2 and S-3) are
 * not used as a top fuel type.
 * @param zoneUnitFuelStats
 * @returns FireZoneFuelStats array
 */
export const getTopFuelsByArea = (zoneUnitFuelStats: FireZoneHFIStats, forDate: DateTime): FireZoneFuelStats[] => {
  let fuelAreaStats = zoneUnitFuelStats.fuel_area_stats
  if (isCoreSeason(forDate)) {
    fuelAreaStats = fuelAreaStats.filter(stat => !SLASH_FUEL_TYPES.includes(stat.fuel_type.fuel_type_code))
  }

  const groupedByFuelType = groupBy(fuelAreaStats, stat => stat.fuel_type.fuel_type_code)
  const fuelTypeAreas = Object.entries(groupedByFuelType).map(([fuelType, entries]) => ({
    fuelType,
    fuelTypeTotalHfi: entries.reduce((sum, entry) => sum + entry.area, 0),
    entries
  }))
  const sortedFuelTypes = fuelTypeAreas.toSorted((a, b) => b.fuelTypeTotalHfi - a.fuelTypeTotalHfi)
  const totalHighHFIArea = fuelAreaStats.reduce((total, stats) => total + stats.area, 0)
  const topFuelsByArea: FireZoneFuelStats[] = []
  let highHFIArea = 0

  for (const { fuelTypeTotalHfi, entries } of sortedFuelTypes) {
    highHFIArea += fuelTypeTotalHfi
    topFuelsByArea.push(...entries)

    if (highHFIArea / totalHighHFIArea > 0.75) {
      break
    }
  }

  return topFuelsByArea
}

export const getZoneMinWindStatsText = (selectedFireZoneUnitMinWindSpeeds: AdvisoryMinWindStats[]) => {
  if (!isEmpty(selectedFireZoneUnitMinWindSpeeds)) {
    const zoneMinWindSpeedsText = calculateWindSpeedText(selectedFireZoneUnitMinWindSpeeds)
    return zoneMinWindSpeedsText
  }
}

const SerifTypography = styled(Typography)({
  fontSize: '1.2rem',
  fontFamily: '"Courier", "Monospace"'
}) as typeof Typography

interface AdvisoryTextProps {
  issueDate: DateTime | null
  forDate: DateTime
  selectedFireCenter?: FireCenter
  advisoryThreshold: number
  selectedFireZoneUnit?: FireShape
}

const AdvisoryText = ({
  issueDate,
  forDate,
  selectedFireCenter,
  advisoryThreshold,
  selectedFireZoneUnit
}: AdvisoryTextProps) => {
  // selectors
  const provincialSummary = useSelector(selectProvincialSummary)
  const filteredFireCentreHFIFuelStats = useSelector(selectFilteredFireCentreHFIFuelStats)

  // derived state
  const selectedFilteredZoneUnitFuelStats = useMemo<FireZoneHFIStats>(() => {
    if (
      isUndefined(filteredFireCentreHFIFuelStats) ||
      isEmpty(filteredFireCentreHFIFuelStats) ||
      isUndefined(selectedFireCenter) ||
      isUndefined(selectedFireZoneUnit)
    ) {
      return { fuel_area_stats: [], min_wind_stats: [] }
    }
    const allFilteredZoneUnitFuelStats = filteredFireCentreHFIFuelStats[selectedFireCenter.name]
    return (
      allFilteredZoneUnitFuelStats?.[selectedFireZoneUnit.fire_shape_id] ?? {
        fuel_area_stats: [],
        min_wind_stats: []
      }
    )
  }, [filteredFireCentreHFIFuelStats, selectedFireZoneUnit])

  const selectedFireZoneUnitTopFuels = useMemo<FireZoneFuelStats[]>(() => {
    return getTopFuelsByArea(selectedFilteredZoneUnitFuelStats, forDate)
  }, [selectedFilteredZoneUnitFuelStats, forDate])

  const highHFIFuelsByProportion = useMemo<FireZoneFuelStats[]>(() => {
    return getTopFuelsByProportion(selectedFilteredZoneUnitFuelStats.fuel_area_stats)
  }, [selectedFilteredZoneUnitFuelStats])

  const selectedFireZoneUnitMinWindSpeeds = selectedFilteredZoneUnitFuelStats.min_wind_stats

  const {
    minStartTime,
    maxEndTime,
    duration: criticalHoursDuration
  } = useMemo(() => {
    return getMinStartAndMaxEndTime(selectedFireZoneUnitTopFuels)
  }, [selectedFireZoneUnitTopFuels])

  const getZoneStatus = () => {
    if (selectedFireCenter) {
      const fireCenterSummary = provincialSummary[selectedFireCenter.name]
      const fireZoneUnitInfos = fireCenterSummary?.filter(
        fc => fc.fire_shape_id === selectedFireZoneUnit?.fire_shape_id
      )
      const zoneStatus = calculateStatusText(fireZoneUnitInfos, advisoryThreshold)
      return zoneStatus
    }
  }

  const zoneStatus = useMemo(
    () => getZoneStatus(),
    [selectedFireCenter, selectedFireZoneUnit, provincialSummary, advisoryThreshold]
  )

  const getCommaSeparatedString = (array: string[]): string => {
    // Slice off the last two items and join then with ' and ' to create a new string. Then take the first n-2 items and
    // deconstruct them into a new array along with the new string. Finally, join the items in the new array with ', '.
    const joinedFuelTypes = [...array.slice(0, -2), array.slice(-2).join(' and ')].join(', ')
    return joinedFuelTypes
  }

  const getTopFuelsString = () => {
    const topFuelCodes = [...new Set(selectedFireZoneUnitTopFuels.map(topFuel => topFuel.fuel_type.fuel_type_code))]
    const lowercaseZoneStatus = zoneStatus?.toLowerCase()
    switch (topFuelCodes.length) {
      case 0:
        return ''
      case 1:
        return `${topFuelCodes[0]} is the most prevalent fuel type under ${lowercaseZoneStatus}.`
      case 2:
        return `${topFuelCodes[0]} and ${topFuelCodes[1]} are the most prevalent fuel types under ${lowercaseZoneStatus}.`
      default:
        return `${getCommaSeparatedString(topFuelCodes)} are the most prevalent fuel types under ${lowercaseZoneStatus}.`
    }
  }

  const getHighProportionFuelsString = (): string => {
    const topFuelCodes = new Set(selectedFireZoneUnitTopFuels.map(topFuel => topFuel.fuel_type.fuel_type_code))

    const highProportionFuels = [
      ...new Set(
        highHFIFuelsByProportion
          .filter(fuel => !topFuelCodes.has(fuel.fuel_type.fuel_type_code))
          .map(fuel_type => fuel_type.fuel_type.fuel_type_code)
      )
    ]
    switch (highProportionFuels.length) {
      case 0:
        return ''
      case 1:
        return `${highProportionFuels[0]} occupies a small portion of the zone but is expected to challenge suppression wherever it occurs.\n\n`
      case 2:
        return `${highProportionFuels[0]} and ${highProportionFuels[1]} occupy a small portion of the zone but are expected to challenge suppression wherever they occur.\n\n`
      default:
        return `${getCommaSeparatedString(highProportionFuels)} occupy a small portion of the zone but are expected to challenge suppression wherever they occur.\n\n`
    }
  }

  const getAdditionalDetailText = (minStartTime?: number, maxEndTime?: number): React.ReactNode => {
    const isEarlyAdvisory = minStartTime !== undefined && minStartTime < 12
    const isOvernightBurnPossible =
      minStartTime !== undefined &&
      maxEndTime !== undefined &&
      (maxEndTime > 23 || criticalHoursExtendToNextDay(minStartTime, maxEndTime))
    const showSlashMessage = !isUndefined(criticalHoursDuration) && criticalHoursDuration > 12
    return (
      <>
        {isEarlyAdvisory && (
          <SerifTypography component="span" data-testid="early-advisory-text">
            Be prepared for fire behaviour to increase early in the day
            {!isOvernightBurnPossible && '.'}
          </SerifTypography>
        )}
        {isEarlyAdvisory && isOvernightBurnPossible && ' '}
        {isOvernightBurnPossible && (
          <SerifTypography component="span" data-testid="overnight-burning-text">
            {isEarlyAdvisory
              ? 'and remain elevated into the overnight hours.'
              : 'Be prepared for fire behaviour to remain elevated into the overnight hours.'}
          </SerifTypography>
        )}
        {(isEarlyAdvisory || isOvernightBurnPossible) && ' '}
        {showSlashMessage && (
          <SerifTypography component="span" data-testid="advisory-message-slash">
            {'Slash fuel types will exhibit high fire intensity throughout the burning period.'}
          </SerifTypography>
        )}
      </>
    )
  }

  const renderDefaultMessage = () => {
    return (
      <>
        {issueDate?.isValid ? (
          <SerifTypography data-testid="default-message">Please select a fire center.</SerifTypography>
        ) : (
          <SerifTypography data-testid="no-data-message">
            No advisory data available for the selected date.
          </SerifTypography>
        )}
      </>
    )
  }

  const renderAdvisoryText = () => {
    const zoneTitle = `${selectedFireZoneUnit?.mof_fire_zone_name}:\n\n`
    const forToday = forDate.toISODate() === DateTime.now().toISODate()
    const displayForDate = forToday ? 'today' : forDate.toLocaleString({ month: 'short', day: 'numeric' })
    const minWindSpeedText = getZoneMinWindStatsText(selectedFireZoneUnitMinWindSpeeds)

    const formattedWindText = minWindSpeedText ? (
      <SerifTypography component="span" data-testid="advisory-message-wind-speed">
        {' '}
        {minWindSpeedText}
      </SerifTypography>
    ) : null

    const hasCriticalHours = !isNil(minStartTime) && !isNil(maxEndTime)
    let message: React.ReactNode = null
    if (hasCriticalHours) {
      const [formattedStartTime, formattedEndTime] = formatCriticalHoursTimeText(minStartTime, maxEndTime, false)
      message = (
        <>
          There is a fire behaviour {zoneStatus?.toLowerCase()} in effect for {selectedFireZoneUnit?.mof_fire_zone_name}{' '}
          between {formattedStartTime} and {formattedEndTime}
          {formattedWindText}. {getTopFuelsString()}
          <br />
          <br />
        </>
      )
    } else {
      message = (
        <>
          There is a fire behaviour {zoneStatus?.toLowerCase()} in effect for {selectedFireZoneUnit?.mof_fire_zone_name}
          {formattedWindText}. {getTopFuelsString()}
          <br />
          <br />
        </>
      )
    }

    const earlyOvernightBurning = getAdditionalDetailText(minStartTime, maxEndTime)

    return (
      <>
        {selectedFireZoneUnit && (
          <SerifTypography data-testid="fire-zone-unit-bulletin" sx={{ whiteSpace: 'pre-wrap' }}>
            {zoneTitle}
          </SerifTypography>
        )}

        {issueDate?.isValid && (
          <SerifTypography data-testid="bulletin-issue-date" sx={{ whiteSpace: 'pre-wrap' }}>
            {`Issued on ${issueDate?.toLocaleString(DateTime.DATETIME_FULL)} for ${displayForDate}.\n\n`}
          </SerifTypography>
        )}

        {!isUndefined(zoneStatus) ? (
          <>
            {zoneStatus === AdvisoryStatus.ADVISORY && (
              <SerifTypography sx={{ whiteSpace: 'pre-line' }} data-testid="advisory-message-advisory">
                {message}
              </SerifTypography>
            )}

            {zoneStatus === AdvisoryStatus.WARNING && (
              <SerifTypography sx={{ whiteSpace: 'pre-line' }} data-testid="advisory-message-warning">
                {message}
              </SerifTypography>
            )}

            <SerifTypography sx={{ whiteSpace: 'pre-line' }} data-testid="advisory-message-proportion">
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
    )
  }

  return (
    <div data-testid="advisory-text">
      <Box
        sx={{
          maxWidth: '100%',
          overflow: 'auto',
          border: '1px solid #ccc',
          padding: 2,
          borderRadius: 1,
          backgroundColor: 'white',
          marginBottom: '10px'
        }}
      >
        {!selectedFireCenter || !issueDate?.isValid || !selectedFireZoneUnit
          ? renderDefaultMessage()
          : renderAdvisoryText()}
      </Box>
    </div>
  )
}

export default AdvisoryText
