import React from 'react'
import { useTheme } from '@mui/material/styles'
import Grid from '@mui/material/Unstable_Grid2'
import Typography from '@mui/material/Typography'
import ElevationFlag from 'features/fba/components/viz/ElevationFlag'
import ElevationLabel from 'features/fba/components/viz/ElevationLabel'
import TPIMountain from 'features/fba/components/viz/TPIMountain'
import { Box } from '@mui/material'
import { FireZoneTPIStats } from '@/api/fbaAPI'

enum ElevationOption {
  BOTTOM = 'Valley Bottom',
  MID = 'Mid Slope',
  Upper = 'Upper Slope'
}

interface ElevationStatusProps {
  tpiStats: Required<FireZoneTPIStats>
}

const ElevationStatus = ({ tpiStats }: ElevationStatusProps) => {
  const theme = useTheme()
  const total = tpiStats.mid_slope + tpiStats.upper_slope + tpiStats.valley_bottom
  const mid_percent = tpiStats.mid_slope === 0 ? 0 : Math.round((tpiStats.mid_slope / total) * 100)
  const upper_percent = tpiStats.upper_slope === 0 ? 0 : Math.round((tpiStats.upper_slope / total) * 100)
  const bottom_percent = tpiStats.valley_bottom === 0 ? 0 : Math.round((tpiStats.valley_bottom / total) * 100)
  return (
    <Box sx={{ paddingBottom: theme.spacing(2), paddingTop: theme.spacing(2) }} data-testid="elevation-status">
      <Grid container sx={{ minHeight: theme.spacing(19) }} xs={12}>
        <Grid container sx={{ paddingRight: theme.spacing(2) }} xs={4}>
          <Grid sx={{ alignItems: 'center', display: 'flex', height: '25%', justifyContent: 'flex-end' }} xs={12}>
            <Typography
              sx={{
                fontSize: '0.75em',
                textAlign: 'right',
                fontWeight: 'bold',
                maxWidth: '75%'
              }}
            >
              Topographic Position:
            </Typography>
          </Grid>
          <ElevationLabel label={ElevationOption.Upper} />
          <ElevationLabel label={ElevationOption.MID} />
          <ElevationLabel label={ElevationOption.BOTTOM} />
        </Grid>
        <Grid container sx={{ alignItems: 'flex-end', display: 'flex' }} xs={4} data-testid="tpi-mountain">
          <Grid sx={{ display: 'flex', alignItems: 'flex-end', height: '80%', justifyContent: 'center' }} xs={12}>
            <TPIMountain />
          </Grid>
        </Grid>
        <Grid container sx={{ paddingLeft: theme.spacing(2) }} xs={4}>
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
          <ElevationFlag percent={upper_percent} testId="upper-slope" />
          <ElevationFlag percent={mid_percent} testId="mid-slope" />
          <ElevationFlag percent={bottom_percent} testId="valley-bottom" />
        </Grid>
      </Grid>
    </Box>
  )
}

export default ElevationStatus
