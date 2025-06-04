import { selectFireCentreHFIFuelStats } from '@/app/rootReducer'
import { calculateStatusText, calculateWindSpeedText } from '@/features/fba/calculateZoneStatus'
import {
  criticalHoursExtendToNextDay,
  formatCriticalHoursTimeText,
  getMinStartAndMaxEndTime
} from '@/features/fba/criticalHoursStartEndTime'
import { Box, Typography } from '@mui/material'
import {
  AdvisoryMinWindStats,
  FireCenter,
  FireCentreHFIStats,
  FireShape,
  FireZoneFuelStats,
  FireZoneHFIStats
} from 'api/fbaAPI'
import { selectProvincialSummary } from 'features/fba/slices/provincialSummarySlice'
import { groupBy, isEmpty, isNil, isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import React, { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import { AdvisoryStatus } from 'utils/constants'

// Minimum area of a fuel type to be included in hfi stats.
// Based on 100 pixels at a 2000m resolution fuel raster measured in square meters.
const FUEL_AREA_THRESHOLD = 100 * 2000 * 2000
const FUEL_TYPES_ALWAYS_INCLUDED = ['C-5', 'S-1', 'S-2', 'S-3']
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

/**
 * Filters out fuel types which cover less than 100 pixels at a 2km resolution but always includes
 * all slash fuel types and C5 regardless of their spatial coverage with respect to high HFI area.
 * @returns FireCentreHFIStats with low prevalence fuel types filtered out.
 */
const filterHFIFuelStatsByArea = (fireCentreHFIFuelStats: FireCentreHFIStats) => {
  const filteredFireCentreStats: FireCentreHFIStats = {}
  for (const [key, value] of Object.entries(fireCentreHFIFuelStats)) {
    const fireZoneStats: { [fire_zone_id: number]: FireZoneHFIStats } = {}
    for (const [key2, value2] of Object.entries(value)) {
      fireZoneStats[parseInt(key2)] = {
        min_wind_stats: value2.min_wind_stats,
        fuel_area_stats: filterHFIStatsByArea(value2.fuel_area_stats)
      }
    }
    filteredFireCentreStats[key] = fireZoneStats
  }
  return filteredFireCentreStats
}

/**
 * Filters out FireZoneFuelStats that do not meet the area threshold but always includes
 * slash and C-5 fuel types regardless of their prevalence.
 * @param stats The FireZoneFuelStats to filter.
 * @returns An array of filtered FireZoneFuelStats.
 */
const filterHFIStatsByArea = (stats: FireZoneFuelStats[]) => {
  return stats.filter(
    stat => stat.fuel_area > FUEL_AREA_THRESHOLD || FUEL_TYPES_ALWAYS_INCLUDED.includes(stat.fuel_type.fuel_type_code)
  )
}

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
  const provincialSummary = useSelector(selectProvincialSummary)
  const { fireCentreHFIFuelStats } = useSelector(selectFireCentreHFIFuelStats)
  const [selectedFireZoneUnitTopFuels, setSelectedFireZoneUnitTopFuels] = useState<FireZoneFuelStats[]>([])
  const [selectedFireZoneUnitMinWindSpeeds, setSelectedFireZoneUnitMinWindSpeeds] = useState<AdvisoryMinWindStats[]>([])
  const [filteredFireCentreHFIFuelStats, setFilteredFireCentreHFIFuelStats] = useState<FireCentreHFIStats>({})
  const [minStartTime, setMinStartTime] = useState<number | undefined>(undefined)
  const [maxEndTime, setMaxEndTime] = useState<number | undefined>(undefined)
  const [criticalHoursDuration, setCriticalHoursDuration] = useState<number | undefined>(undefined)
  const [highHFIFuelsByProportion, setHighHFIFuelsByProportion] = useState<FireZoneFuelStats[]>([])

  useEffect(() => {
    if (
      isUndefined(fireCentreHFIFuelStats) ||
      isEmpty(fireCentreHFIFuelStats) ||
      isUndefined(selectedFireCenter) ||
      isUndefined(selectedFireZoneUnit)
    ) {
      setMinStartTime(undefined)
      setMaxEndTime(undefined)
      setHighHFIFuelsByProportion([])
      setFilteredFireCentreHFIFuelStats({})
      return
    }
    const allZoneUnitFuelStats = fireCentreHFIFuelStats?.[selectedFireCenter.name]
    const selectedZoneUnitFuelStats = allZoneUnitFuelStats?.[selectedFireZoneUnit.fire_shape_id] ?? {
      fuel_area_stats: [],
      min_wind_stats: []
    }
    setSelectedFireZoneUnitMinWindSpeeds(selectedZoneUnitFuelStats.min_wind_stats)
    const topFuelsByProportion = getTopFuelsByProportion(selectedZoneUnitFuelStats.fuel_area_stats)
    setHighHFIFuelsByProportion(topFuelsByProportion)
    const newFilteredFireCentreHFIFuelStats = filterHFIFuelStatsByArea(fireCentreHFIFuelStats)
    setFilteredFireCentreHFIFuelStats(newFilteredFireCentreHFIFuelStats)
  }, [fireCentreHFIFuelStats, selectedFireZoneUnit])

  useEffect(() => {
    if (
      isUndefined(filteredFireCentreHFIFuelStats) ||
      isEmpty(filteredFireCentreHFIFuelStats) ||
      isUndefined(selectedFireCenter) ||
      isUndefined(selectedFireZoneUnit)
    ) {
      setSelectedFireZoneUnitTopFuels([])
      return
    }

    const allFilteredZoneUnitFuelStats = filteredFireCentreHFIFuelStats?.[selectedFireCenter.name]
    const selectedFilteredZoneUnitFuelStats = allFilteredZoneUnitFuelStats?.[selectedFireZoneUnit.fire_shape_id] ?? {
      fuel_area_stats: [],
      min_wind_stats: []
    }
    const topFuels = getTopFuelsByArea(selectedFilteredZoneUnitFuelStats, forDate)
    setSelectedFireZoneUnitTopFuels(topFuels)
  }, [filteredFireCentreHFIFuelStats])

  useEffect(() => {
    const { minStartTime, maxEndTime, duration } = getMinStartAndMaxEndTime(selectedFireZoneUnitTopFuels)
    setMinStartTime(minStartTime)
    setMaxEndTime(maxEndTime)
    setCriticalHoursDuration(duration)
  }, [selectedFireZoneUnitTopFuels])

  const getCommaSeparatedString = (array: string[]): string => {
    // Slice off the last two items and join then with ' and ' to create a new string. Then take the first n-2 items and
    // deconstruct them into a new array along with the new string. Finally, join the items in the new array with ', '.
    const joinedFuelTypes = [...array.slice(0, -2), array.slice(-2).join(' and ')].join(', ')
    return joinedFuelTypes
  }

  const getTopFuelsString = () => {
    const topFuelCodes = [...new Set(selectedFireZoneUnitTopFuels.map(topFuel => topFuel.fuel_type.fuel_type_code))]
    const zoneStatus = getZoneStatus()?.toLowerCase()
    switch (topFuelCodes.length) {
      case 0:
        return ''
      case 1:
        return `${topFuelCodes[0]} is the most prevalent fuel type under ${zoneStatus}.`
      case 2:
        return `${topFuelCodes[0]} and ${topFuelCodes[1]} are the most prevalent fuel types under ${zoneStatus}.`
      default:
        return `${getCommaSeparatedString(topFuelCodes)} are the most prevalent fuel types under ${zoneStatus}.`
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
          <Typography component="span" data-testid="early-advisory-text">
            Be prepared for fire behaviour to increase early in the day
            {!isOvernightBurnPossible && '.'}
          </Typography>
        )}
        {isEarlyAdvisory && isOvernightBurnPossible && ' '}
        {isOvernightBurnPossible && (
          <Typography component="span" data-testid="overnight-burning-text">
            {isEarlyAdvisory
              ? 'and remain elevated into the overnight hours.'
              : 'Be prepared for fire behaviour to remain elevated into the overnight hours.'}
          </Typography>
        )}
        {(isEarlyAdvisory || isOvernightBurnPossible) && ' '}
        {showSlashMessage && (
          <Typography component="span" data-testid="advisory-message-slash">
            {'Slash fuel types will exhibit high fire intensity throughout the burning period.'}
          </Typography>
        )}
      </>
    )
  }

  const renderDefaultMessage = () => {
    return (
      <>
        {issueDate?.isValid ? (
          <Typography data-testid="default-message">Please select a fire center.</Typography>
        ) : (
          <Typography data-testid="no-data-message">No advisory data available for the selected date.</Typography>
        )}
      </>
    )
  }

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

  const renderAdvisoryText = () => {
    const zoneTitle = `${selectedFireZoneUnit?.mof_fire_zone_name}:\n\n`
    const forToday = forDate.toISODate() === DateTime.now().toISODate()
    const displayForDate = forToday ? 'today' : forDate.toLocaleString({ month: 'short', day: 'numeric' })
    const zoneStatus = getZoneStatus()
    const minWindSpeedText = getZoneMinWindStatsText(selectedFireZoneUnitMinWindSpeeds)

    const formattedWindText = minWindSpeedText ? (
      <Typography component="span" data-testid="advisory-message-wind-speed">
        {' '}
        {minWindSpeedText}
      </Typography>
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
          <Typography data-testid="fire-zone-unit-bulletin" sx={{ whiteSpace: 'pre-wrap' }}>
            {zoneTitle}
          </Typography>
        )}

        {issueDate?.isValid && (
          <Typography data-testid="bulletin-issue-date" sx={{ whiteSpace: 'pre-wrap' }}>
            {`Issued on ${issueDate?.toLocaleString(DateTime.DATETIME_FULL)} for ${displayForDate}.\n\n`}
          </Typography>
        )}

        {!isUndefined(zoneStatus) ? (
          <>
            {zoneStatus === AdvisoryStatus.ADVISORY && (
              <Typography sx={{ whiteSpace: 'pre-line' }} data-testid="advisory-message-advisory">
                {message}
              </Typography>
            )}

            {zoneStatus === AdvisoryStatus.WARNING && (
              <Typography sx={{ whiteSpace: 'pre-line' }} data-testid="advisory-message-warning">
                {message}
              </Typography>
            )}

            <Typography sx={{ whiteSpace: 'pre-line' }} data-testid="advisory-message-proportion">
              {getHighProportionFuelsString()}
            </Typography>

            {earlyOvernightBurning && <>{earlyOvernightBurning}</>}

            {!hasCriticalHours && (
              <Typography data-testid="advisory-message-no-critical-hours">No critical hours available.</Typography>
            )}
          </>
        ) : (
          <Typography data-testid="no-advisory-message">
            No advisories or warnings issued for the selected fire zone unit.
          </Typography>
        )}
      </>
    )
  }

  return (
    <div data-testid="advisory-text">
      <Box
        sx={{
          height: 350,
          maxWidth: '100%',
          overflow: 'auto',
          border: '1px solid #ccc',
          padding: 2,
          borderRadius: 1,
          backgroundColor: 'white'
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
