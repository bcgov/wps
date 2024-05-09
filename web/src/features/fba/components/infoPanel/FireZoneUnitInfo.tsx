import React from 'react'
import { Box, ListItem, ListItemIcon, Typography } from '@mui/material'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from 'features/fba/components/map/featureStylers'
import { LIGHT_GREY } from 'app/theme'
import { FireShapeAreaDetail } from 'api/fbaAPI'

interface FireZoneUnitInfoProps {
  advisoryThreshold: number
  fireZoneUnitName: string
  fireZoneUnitDetails: FireShapeAreaDetail[]
}

const FireZoneUnitInfo = ({ advisoryThreshold, fireZoneUnitName, fireZoneUnitDetails }: FireZoneUnitInfoProps) => {
  const calculateStatus = (details: FireShapeAreaDetail[]) => {
    let status = LIGHT_GREY

    if (details.length === 0) {
      return status
    }

    const advisoryThresholdDetail = details.find(detail => detail.threshold == 1)
    const warningThresholdDetail = details.find(detail => detail.threshold == 2)
    const combustibleArea = details[0].combustible_area
    const advisoryArea = advisoryThresholdDetail?.elevated_hfi_area ?? 0
    const warningArea = warningThresholdDetail?.elevated_hfi_area ?? 0
    const advisoryPercentage = (advisoryArea / combustibleArea) * 100
    const warningPercentage = (warningArea / combustibleArea) * 100

    if (advisoryPercentage + warningPercentage > advisoryThreshold) {
      // advisory color orange
      status = ADVISORY_ORANGE_FILL
    }

    if (warningPercentage > advisoryThreshold) {
      // advisory color red
      status = ADVISORY_RED_FILL
    }

    return status
  }

  return (
    <ListItem data-testid="fire-zone-unit-info" sx={{ paddingBottom: '0px', paddingTop: '0px' }}>
      <ListItemIcon sx={{ minWidth: '24px' }}>
        <Box
          data-testid="fire-zone-unit-info-swatch"
          sx={{ backgroundColor: calculateStatus(fireZoneUnitDetails), height: '0.7rem', width: '1rem' }}
        />
      </ListItemIcon>
      <Typography sx={{ fontSize: '0.75rem' }}>{fireZoneUnitName}</Typography>
    </ListItem>
  )
}

export default FireZoneUnitInfo
