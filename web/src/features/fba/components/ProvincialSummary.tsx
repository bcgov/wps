import React from 'react'

import { Box, Typography } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import Grid from '@mui/material/Unstable_Grid2'
import { Container } from 'components'
import FireCentreInfo, { FireZoneCentreInfo } from 'features/fba/components/FireCentreInfo'

const fireZoneCentreDetails: FireZoneCentreInfo[] = [
  {
    fireCentreName: 'Cariboo FC',
    fireZoneUnits: [
      { fireZoneUnitName: 'C1 - Quesnel', status: 0 },
      { fireZoneUnitName: 'C2/C3 - Central Cariboo', status: 0 },
      { fireZoneUnitName: 'C4 - 100 Mile House', status: 0 },
      { fireZoneUnitName: 'C5 - Chilcotin', status: 0 }
    ]
  },
  {
    fireCentreName: 'Kamloops FC',
    fireZoneUnits: [
      { fireZoneUnitName: 'K2 - Kamloops', status: 1 },
      { fireZoneUnitName: 'K4 - Vernon', status: 1 },
      { fireZoneUnitName: 'K5 - Penticton', status: 1 },
      { fireZoneUnitName: 'K6 - Merritt', status: 2 },
      { fireZoneUnitName: 'K7 - Lillooet', status: 2 }
    ]
  }
]

const ProvincialSummary = () => {
  const theme = useTheme()
  return (
    <Grid container>
      <Grid xs={12}>
        <Box sx={{ backgroundColor: '#e4e4e5', paddingTop: '8px', paddingBottom: '8px' }}>
          <Typography
            sx={{
              color: theme.palette.primary.main,
              fontWeight: 'bold',
              paddingLeft: '1.25rem'
            }}
            variant="h6"
          >
            Provincial Summary
          </Typography>
        </Box>
        <Box>
          {fireZoneCentreDetails.map(fireCentre => {
            return (
              <FireCentreInfo
                key={fireCentre.fireCentreName}
                fireCentreName={fireCentre.fireCentreName}
                fireZoneUnits={fireCentre.fireZoneUnits}
              />
            )
          })}
        </Box>
      </Grid>
    </Grid>
  )
}

export default ProvincialSummary
