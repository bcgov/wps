import React from 'react'
import { Typography } from '@mui/material'
import Grid from '@mui/material/Grid'
import Flag from '@/features/fba/components/viz/FillableFlag'

interface ElevationFlagProps {
  id: string
  percent: number
  testId?: string
}

const ElevationFlag = ({ id, percent, testId }: ElevationFlagProps) => {
  return (
    <Grid sx={{ alignItems: 'center', display: 'flex', justifyContent: 'flex-end' }} size={6}>
      <Flag maskId={id} percent={percent} />
      <Typography
        sx={{
          fontSize: '1.25em',
          fontWeight: 'bold',
          position: 'absolute',
          right: '60px',
          textShadow: '-2px 2px 4px #FFF, 2px 2px 4px #FFF, 2px -2px 4px #FFF, -2px -2px 4px #FFF'
        }}
        data-testid={testId}
      >
        {percent}%
      </Typography>
    </Grid>
  )
}

export default React.memo(ElevationFlag)
