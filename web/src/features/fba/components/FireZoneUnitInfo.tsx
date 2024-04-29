import React from 'react'
import { Box, ListItem, ListItemIcon, Typography } from '@mui/material'
import { ADVISORY_ORANGE_FILL, ADVISORY_RED_FILL } from 'features/fba/components/map/featureStylers'
import { LIGHT_GREY } from 'app/theme'

interface FireZoneUnitInfoProps {
  fireZoneUnitName: string
  status: 0 | 1 | 2
}

const FireZoneUnitInfo = ({ fireZoneUnitName, status }: FireZoneUnitInfoProps) => {
  const convertStatusToColour = (status: 0 | 1 | 2) => {
    switch (status) {
      case 0:
        return LIGHT_GREY
      case 1:
        return ADVISORY_ORANGE_FILL
      case 2:
        return ADVISORY_RED_FILL
    }
  }

  return (
    <ListItem sx={{ paddingBottom: '0px', paddingTop: '0px' }}>
      <ListItemIcon sx={{ minWidth: '24px' }}>
        <Box sx={{ backgroundColor: convertStatusToColour(status), height: '0.7rem', width: '1rem' }} />
      </ListItemIcon>
      <Typography sx={{ fontSize: '0.75rem' }}>{fireZoneUnitName}</Typography>
    </ListItem>
  )
}

export default FireZoneUnitInfo
