import React from 'react'
import { useTheme } from '@mui/material/styles'
import Grid from '@mui/material/Unstable_Grid2'
import Typography from '@mui/material/Typography'
import ElevationFlag from 'features/fba/components/viz/ElevationFlag'
import ElevationLabel from 'features/fba/components/viz/ElevationLabel'
import TPIMountain from 'features/fba/components/viz/TPIMountain'
import { Box } from '@mui/material'

enum ElevationOption {
  BOTTOM = 'Valley Bottom',
  MID = 'Mid Slope',
  Upper = 'Upper Slope'
}

interface ElevationStatusProps {
  bottom: number
  mid: number
  upper: number
}

const ElevationStatus = ({ bottom, mid, upper }: ElevationStatusProps) => {
  const theme = useTheme()
  return (
    <Box sx={{ paddingBottom: theme.spacing(2), paddingTop: theme.spacing(2) }}>
      <Typography sx={{ fontWeight: 'bold', paddingBottom: theme.spacing(1), textAlign: 'center' }}>
        HFI Distribution by Elevation
      </Typography>
    <Grid container sx={{ minHeight: theme.spacing(19) }} xs={12}>
      <Grid container xs={4}>
        <Grid sx={{ alignItems: 'center', display: 'flex', height: '25%', justifyContent: 'flex-end' }} xs={12}>
          <Typography
            sx={{
              fontSize: '0.75em',
              textAlign: 'right',
              fontWeight: 'bold'
            }}
          >
            Elevation:
          </Typography>
        </Grid>
        <ElevationLabel label={ElevationOption.Upper} />
        <ElevationLabel label={ElevationOption.MID} />
        <ElevationLabel label={ElevationOption.BOTTOM} />
      </Grid>
      <Grid container sx={{ alignItems: 'flex-end', display: 'flex' }} xs={4}>
        <Grid sx={{ display: 'flex', alignItems: 'flex-end', height: '80%', justifyContent: 'center' }} xs={12}>
          <TPIMountain />
        </Grid>
      </Grid>
      <Grid container xs={4}>
        <Grid sx={{ alignItems: 'center', display: 'flex', height: '25%', justifyContent: 'flex-start' }} xs={12}>
          <Typography
            sx={{
              fontSize: '0.75em',
              textAlign: 'left',
              fontWeight: 'bold',
              maxWidth: '75%'
            }}
          >
            Proportion of Advisory Area:
          </Typography>
        </Grid>
        <ElevationFlag percent={upper} />
        <ElevationFlag percent={mid} />
        <ElevationFlag percent={bottom} />
      </Grid>
    </Grid>
    </Box>
  )
}

export default ElevationStatus
