import { Box, Typography } from '@mui/material'
import { FireShape, FireShapeArea } from 'api/fbaAPI'
import { DateTime } from 'luxon'
import React from 'react'
import { AdvisoryStatus } from 'utils/constants'

interface AdvisoryTextProps {
  issueDate: DateTime | null
  forDate: DateTime
  selectedFireZoneUnit: FireShape | undefined
  fireShapeAreas: FireShapeArea[]
  advisoryThreshold: number
}

const AdvisoryText = ({
  issueDate,
  forDate,
  selectedFireZoneUnit,
  fireShapeAreas,
  advisoryThreshold
}: AdvisoryTextProps) => {
  const calculateStatus = (details: FireShapeArea[]): AdvisoryStatus | undefined => {
    const advisoryThresholdDetail = details.find(detail => detail.threshold == 1)
    const warningThresholdDetail = details.find(detail => detail.threshold == 2)
    const advisoryPercentage = advisoryThresholdDetail?.elevated_hfi_percentage ?? 0
    const warningPercentage = warningThresholdDetail?.elevated_hfi_percentage ?? 0

    if (warningPercentage > advisoryThreshold) {
      return AdvisoryStatus.WARNING
    }

    if (advisoryPercentage + warningPercentage > advisoryThreshold) {
      return AdvisoryStatus.ADVISORY
    }

    return
  }

  const zoneDetails = fireShapeAreas.filter(area => area.fire_shape_id == selectedFireZoneUnit?.fire_shape_id)
  const zoneStatus = calculateStatus(zoneDetails)

  const forToday = issueDate?.toISODate() === forDate.toISODate()
  const displayForDate = forToday ? 'today' : forDate.toLocaleString({ month: 'short', day: 'numeric' })

  return (
    <div data-testid="advisory-text">
      <Box
        sx={{
          height: 300,
          maxWidth: '100%',
          overflow: 'auto',
          border: '1px solid #ccc',
          padding: 2,
          borderRadius: 1,
          backgroundColor: 'white'
        }}
      >
        {!issueDate?.isValid && <Typography>No advisories issued for today.</Typography>}
        {issueDate?.isValid && !selectedFireZoneUnit && <Typography>No fire zone selected.</Typography>}
        {selectedFireZoneUnit && issueDate?.isValid && !zoneStatus && (
          <Typography>No advisory/warning issued for the selected zone.</Typography>
        )}
        {zoneStatus && selectedFireZoneUnit && (
          <>
            <Typography
              sx={{ whiteSpace: 'pre-wrap' }}
            >{`Issued on ${issueDate?.toLocaleString(DateTime.DATE_MED)} for ${displayForDate}.\n\n`}</Typography>
            <Typography>{`There is a fire behaviour ${zoneStatus} in effect in the following areas:`}</Typography>
            <ul>
              <li>
                <Typography>{selectedFireZoneUnit.mof_fire_zone_name}</Typography>
              </li>
            </ul>
          </>
        )}
      </Box>
    </div>
  )
}

export default AdvisoryText
