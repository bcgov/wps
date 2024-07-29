import React from 'react'
import { Box, Grid, Typography } from '@mui/material'

const FLAG_COLOUR = '#CCCCCC'

interface ElevationFlagProps {
  percent: number
}

const ElevationFlag = ({ percent }: ElevationFlagProps) => {
  return (
    <Grid sx={{ display: 'flex', alignItems: 'center', flexGrow: 1, justifyContent: 'flex-start' }} xs={12}>
      <Box
        sx={{
          alignItems: 'center',
          backgroundImage: `linear-gradient(to right, ${FLAG_COLOUR} ${percent}%, #FFFFFF00 ${percent}%)`,
          border: `1px solid ${FLAG_COLOUR}`,
          clipPath: 'polygon(0 50%, 10% 0, 100% 0, 100% 100%, 10% 100%)',
          display: 'flex',
          height: '32px',
          justifyContent: 'center',
          width: '65%'
        }}
      >
        <Typography sx={{ fontSize: '0.75em' }}>{percent}%</Typography>
      </Box>
    </Grid>
  )
}

export default React.memo(ElevationFlag)
