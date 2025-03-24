import { Box, Typography } from '@mui/material'
import { FireCenter, FireShape, FireZoneFuelStats } from 'api/fbaAPI'
import { DateTime } from 'luxon'
import React, { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import { selectProvincialSummary } from 'features/fba/slices/provincialSummarySlice'
import { selectFireCentreHFIFuelStats } from '@/app/rootReducer'
import { AdvisoryStatus } from 'utils/constants'
import { groupBy, isEmpty, isNil, isUndefined } from 'lodash'
import { calculateStatusText } from '@/features/fba/calculateZoneStatus'

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
 * Returns the fuel type stat records that cumulatively account for more than 75% of total area with high HFI.
 * The zoneUnitFuelStats may contain more than 1 record for each fuel type, if there are pixels matching both
 * HFI class 5 and 6 for that fuel type.
 * @param zoneUnitFuelStats
 * @returns FireZoneFuelStats array
 */
export const getTopFuelsByArea = (zoneUnitFuelStats: FireZoneFuelStats[]): FireZoneFuelStats[] => {
  const groupedByFuelType = groupBy(zoneUnitFuelStats, stat => stat.fuel_type.fuel_type_code)

  const fuelTypeAreas = Object.entries(groupedByFuelType).map(([fuelType, entries]) => ({
    fuelType,
    fuelTypeTotalHfi: entries.reduce((sum, entry) => sum + entry.area, 0),
    entries
  }))

  const sortedFuelTypes = fuelTypeAreas.toSorted((a, b) => b.fuelTypeTotalHfi - a.fuelTypeTotalHfi)
  const totalHighHFIArea = zoneUnitFuelStats.reduce((total, stats) => total + stats.area, 0)

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

  const [minStartTime, setMinStartTime] = useState<number | undefined>(undefined)
  const [maxEndTime, setMaxEndTime] = useState<number | undefined>(undefined)
  const [highHFIFuelsByProportion, setHighHFIFuelsByProportion] = useState<FireZoneFuelStats[]>([])

  useEffect(() => {
    if (
      isUndefined(fireCentreHFIFuelStats) ||
      isEmpty(fireCentreHFIFuelStats) ||
      isUndefined(selectedFireCenter) ||
      isUndefined(selectedFireZoneUnit)
    ) {
      setSelectedFireZoneUnitTopFuels([])
      setMinStartTime(undefined)
      setMaxEndTime(undefined)
      setHighHFIFuelsByProportion([])
      return
    }
    const allZoneUnitFuelStats = fireCentreHFIFuelStats?.[selectedFireCenter.name]
    const selectedZoneUnitFuelStats = allZoneUnitFuelStats?.[selectedFireZoneUnit.fire_shape_id] ?? []
    const topFuels = getTopFuelsByArea(selectedZoneUnitFuelStats)
    setSelectedFireZoneUnitTopFuels(topFuels)
    const topFuelsByProportion = getTopFuelsByProportion(selectedZoneUnitFuelStats)
    setHighHFIFuelsByProportion(topFuelsByProportion)
  }, [fireCentreHFIFuelStats, selectedFireZoneUnit])

  useEffect(() => {
    let startTime: number | undefined = undefined
    let endTime: number | undefined = undefined
    for (const fuel of selectedFireZoneUnitTopFuels) {
      if (!isUndefined(fuel.critical_hours.start_time)) {
        if (isUndefined(startTime) || fuel.critical_hours.start_time < startTime) {
          startTime = fuel.critical_hours.start_time
        }
      }
      if (!isUndefined(fuel.critical_hours.end_time)) {
        if (isUndefined(endTime) || fuel.critical_hours.end_time > endTime) {
          endTime = fuel.critical_hours.end_time
        }
      }
    }
    setMinStartTime(startTime)
    setMaxEndTime(endTime)
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
        return `Fuel type ${topFuelCodes[0]} is the most prevalent fuel type under ${zoneStatus} that you will encounter.`
      case 2:
        return `Fuel types ${topFuelCodes[0]} and ${topFuelCodes[1]} are the most prevalent fuel types under ${zoneStatus} that you will encounter.`
      default:
        return `Fuel types ${getCommaSeparatedString(topFuelCodes)} are the most prevalent fuel types under ${zoneStatus} that you will encounter.`
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
        return `Also watch out for fuel type ${highProportionFuels[0]} which occupies a small portion of the zone but is expected to be under advisory conditions wherever it occurs.`
      case 2:
        return `Also watch out for fuel types ${highProportionFuels[0]} and ${highProportionFuels[1]} which occupy a small portion of the zone but are expected to be under advisory conditions wherever they occur.`
      default:
        return `Also watch out for fuel types ${getCommaSeparatedString(highProportionFuels)} which occupy a small portion of the zone but are expected to be under advisory conditions wherever they occur.`
    }
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
    const hasCriticalHours = !isNil(minStartTime) && !isNil(maxEndTime) && selectFireCentreHFIFuelStats.length > 0
    let message = ''
    if (hasCriticalHours) {
      message = `There is a fire behaviour ${zoneStatus} in effect for ${selectedFireZoneUnit?.mof_fire_zone_name} between ${minStartTime}:00 and ${maxEndTime}:00. ${getTopFuelsString()}\n\n`
    } else {
      message = `There is a fire behaviour ${zoneStatus} in effect for ${selectedFireZoneUnit?.mof_fire_zone_name}.\n\n`
    }

    return (
      <>
        {selectedFireZoneUnit && (
          <Typography data-testid="fire-zone-unit-bulletin" sx={{ whiteSpace: 'pre-wrap' }}>
            {zoneTitle}
          </Typography>
        )}
        {issueDate?.isValid && (
          <Typography
            data-testid="bulletin-issue-date"
            sx={{ whiteSpace: 'pre-wrap' }}
          >{`Issued on ${issueDate?.toLocaleString(DateTime.DATETIME_FULL_WITH_SECONDS)} for ${displayForDate}.\n\n`}</Typography>
        )}
        {!isUndefined(zoneStatus) && zoneStatus === AdvisoryStatus.ADVISORY && (
          <Typography sx={{ whiteSpace: 'pre-line' }} data-testid="advisory-message-advisory">
            {message}
          </Typography>
        )}
        {!isUndefined(zoneStatus) && zoneStatus === AdvisoryStatus.WARNING && (
          <Typography sx={{ whiteSpace: 'pre-line' }} data-testid="advisory-message-warning">
            {message}
          </Typography>
        )}
        {!isUndefined(zoneStatus) && (
          <Typography sx={{ whiteSpace: 'pre-line' }} data-testid="advisory-message-proportion">
            {getHighProportionFuelsString()}
          </Typography>
        )}
        {!hasCriticalHours && !isUndefined(zoneStatus) && (
          <Typography data-testid="advisory-message-no-critical-hours">No critical hours available.</Typography>
        )}
        {isUndefined(zoneStatus) && (
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
