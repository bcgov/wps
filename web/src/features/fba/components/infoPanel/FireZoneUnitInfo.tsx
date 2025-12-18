import React from 'react'
import { Box, ListItem, ListItemIcon, Typography } from '@mui/material'
import { FireShapeStatusDetail } from 'api/fbaAPI'
import { useTheme } from '@mui/material/styles'
import { TRANSPARENT_COLOUR } from 'app/theme'
import { calculateStatusColour } from '@/features/fba/calculateZoneStatus'

interface FireZoneUnitInfoProps {
  fireZoneUnitName: string
  fireZoneUnitDetails: FireShapeStatusDetail
}

const FireZoneUnitInfo = ({ fireZoneUnitName, fireZoneUnitDetails }: FireZoneUnitInfoProps) => {
  const theme = useTheme()

  return (
    <ListItem data-testid="fire-zone-unit-info" sx={{ paddingBottom: theme.spacing(1), paddingTop: '0px' }}>
      <ListItemIcon sx={{ minWidth: '24px' }}>
        <Box
          data-testid="fire-zone-unit-info-swatch"
          sx={{
            backgroundColor: calculateStatusColour(fireZoneUnitDetails, TRANSPARENT_COLOUR),
            border: '1px solid #777',
            height: '0.7rem',
            width: '1rem'
          }}
        />
      </ListItemIcon>
      <Typography>{fireZoneUnitName}</Typography>
    </ListItem>
  )
}

export default FireZoneUnitInfo
