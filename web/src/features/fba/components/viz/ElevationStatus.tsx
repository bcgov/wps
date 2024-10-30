import React from 'react'
import { useTheme } from '@mui/material/styles'
import Grid from '@mui/material/Unstable_Grid2'
import Typography from '@mui/material/Typography'
import ElevationFlag from 'features/fba/components/viz/ElevationFlag'
import ElevationLabel from 'features/fba/components/viz/ElevationLabel'
import { Box } from '@mui/material'
import { FireZoneTPIStats } from '@/api/fbaAPI'
import Mountain from 'features/fba/images/mountain.png'

enum ElevationOption {
  BOTTOM = 'Valley Bottom',
  MID = 'Mid Slope',
  UPPER = 'Upper Slope'
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
    <Grid container xs={12} data-testid="elevation-status">
      <Grid container sx={{ height: theme.spacing(6) }} xs={12}>
        <Grid sx={{ paddingLeft: theme.spacing(0.5), paddingRight: theme.spacing(0.5) }} xs={6}>
          <Typography
            sx={{
              color: '#003366',
              fontWeight: 'bold',
              textAlign: 'left',
              width: '50%'
            }}
          >
            Topographic Position:
          </Typography>
        </Grid>
        <Grid sx={{ display: 'flex', justifyContent: 'flex-end' }} xs={6}>
          <Typography
            sx={{
              color: '#003366',
              fontWeight: 'bold',
              textAlign: 'right',
              width: '65%'
            }}
          >
            Proportion of Advisory Area:
          </Typography>
        </Grid>
      </Grid>
      <Grid xs={12}>
        <Box
          sx={{
            backgroundBlendMode: 'overlay',
            backgroundColor: 'rgba(255, 255, 255, 0.6)',
            background: `url(${Mountain})`,
            backgroundRepeat: 'round',
            display: 'flex',
            width: '100%'
          }}
          data-testid="tpi-mountain"
        >
          <Grid sx={{ paddingLeft: theme.spacing(0.5), paddingRight: theme.spacing(0.5) }} container xs={12}>
            <Grid container sx={{ height: theme.spacing(8) }} xs={12}>
              <ElevationLabel label={ElevationOption.UPPER} />
              <ElevationFlag id="upper" percent={upper_percent} testId="upper-slope" />
            </Grid>
            <Grid container sx={{ height: theme.spacing(8) }} xs={12}>
              <ElevationLabel label={ElevationOption.MID} />
              <ElevationFlag id="mid" percent={mid_percent} testId="mid-slope" />
            </Grid>
            <Grid container sx={{ height: theme.spacing(8) }} xs={12}>
              <ElevationLabel label={ElevationOption.BOTTOM} />
              <ElevationFlag id="lower" percent={bottom_percent} testId="valley-bottom" />
            </Grid>
          </Grid>
        </Box>
      </Grid>
    </Grid>
  )
}

export default ElevationStatus