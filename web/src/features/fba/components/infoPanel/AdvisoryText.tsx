import { Box, Typography } from '@mui/material'
import { FireCenter, FireShape, FireZoneFuelStats } from 'api/fbaAPI'
import { DateTime } from 'luxon'
import React, { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import { selectProvincialSummary } from 'features/fba/slices/provincialSummarySlice'
import { selectFireCentreHFIFuelStats } from '@/app/rootReducer'
import { AdvisoryStatus } from 'utils/constants'
import { isEmpty, isNil, isUndefined, take } from 'lodash'
import { calculateStatusText } from '@/features/fba/calculateZoneStatus'

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

  const sortByArea = (a: FireZoneFuelStats, b: FireZoneFuelStats) => {
    if (a.area > b.area) {
      return -1
    }
    if (a.area < b.area) {
      return 1
    }
    return 0
  }

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
      return
    }
    const allZoneUnitFuelStats = fireCentreHFIFuelStats?.[selectedFireCenter.name]
    const selectedZoneUnitFuelStats = allZoneUnitFuelStats?.[selectedFireZoneUnit.fire_shape_id] ?? []
    const sortedFuelStats = [...selectedZoneUnitFuelStats].sort(sortByArea)
    let topFuels = take(sortedFuelStats, 3)
    setSelectedFireZoneUnitTopFuels(topFuels)
  }, [fireCentreHFIFuelStats])

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

  const getTopFuelsString = () => {
    const topFuelCodes = selectedFireZoneUnitTopFuels.map(topFuel => topFuel.fuel_type.fuel_type_code)
    switch (topFuelCodes.length) {
      case 1:
        return `fuel type ${topFuelCodes[0]}`
      case 2:
        return `fuel types ${topFuelCodes[0]} and ${topFuelCodes[1]}`
      case 3:
        return `fuel types ${topFuelCodes[0]}, ${topFuelCodes[1]} and ${topFuelCodes[2]}`
      default:
        return ''
    }
  }

  const renderDefaultMessage = () => {
    return (
      <>
        {issueDate?.isValid ? (
          <Typography data-testid="default-message">Please select a fire center.</Typography>
        ) : (
          <Typography data-testid="no-data-message">No advisory data available for today.</Typography>
        )}{' '}
      </>
    )
  }

  const renderAdvisoryText = () => {
    const forToday = issueDate?.toISODate() === forDate.toISODate()
    const displayForDate = forToday ? 'today' : forDate.toLocaleString({ month: 'short', day: 'numeric' })

    const fireCenterSummary = provincialSummary[selectedFireCenter!.name]
    const fireZoneUnitInfos = fireCenterSummary?.filter(fc => fc.fire_shape_id === selectedFireZoneUnit?.fire_shape_id)
    const zoneStatus = calculateStatusText(fireZoneUnitInfos, advisoryThreshold)
    const hasCriticalHours = !isNil(minStartTime) && !isNil(maxEndTime) && selectFireCentreHFIFuelStats.length > 0
    let message = ''
    if (hasCriticalHours) {
      message = `There is a fire behaviour ${zoneStatus} in effect for ${selectedFireZoneUnit?.mof_fire_zone_name} between ${minStartTime}:00 and ${maxEndTime}:00 for ${getTopFuelsString()}.`
    } else {
      message = `There is a fire behaviour ${zoneStatus} in effect for ${selectedFireZoneUnit?.mof_fire_zone_name}.`
    }

    return (
      <>
        {issueDate?.isValid && (
          <Typography
            sx={{ whiteSpace: 'pre-wrap' }}
          >{`Issued on ${issueDate?.toLocaleString(DateTime.DATE_MED)} for ${displayForDate}.\n\n`}</Typography>
        )}
        {!isUndefined(zoneStatus) && zoneStatus === AdvisoryStatus.ADVISORY && (
          <Typography data-testid="advisory-message-advisory">{message}</Typography>
        )}
        {!isUndefined(zoneStatus) && zoneStatus === AdvisoryStatus.WARNING && (
          <Typography data-testid="advisory-message-warning">{message}</Typography>
        )}
        {!hasCriticalHours && (
          <Typography data-testid="advisory-message-no-critical-hours" sx={{ paddingTop: '1rem' }}>
            No critical hours available.
          </Typography>
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
