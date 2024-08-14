import React from 'react'
import { Box, Grid, Typography } from '@mui/material'

const FLAG_COLOUR = '#CCCCCC'

interface ElevationFlagProps {
  percent: number
}

const ElevationFlag = ({ percent }: ElevationFlagProps) => {
  return (
    <Grid item sx={{ display: 'flex', alignItems: 'center', flexGrow: 1, justifyContent: 'flex-start' }} xs={12}>
      <Box
        sx={{
          backgroundColor: FLAG_COLOUR,
          clipPath: 'polygon(0 50%, 10% 0, 100% 0, 100% 100%, 10% 100%)',
          height: '32px',
          padding: '1px',
          width: '65%'
        }}>
        <Box
          sx={{
            alignItems: 'center',
            backgroundImage: `linear-gradient(to right, ${FLAG_COLOUR} ${percent}%, #FFFFFFFF ${percent}%)`,
            clipPath: 'polygon(0 50%, 10% 0, 100% 0, 100% 100%, 10% 100%)',
            display: 'flex',
            height: '30px',
            justifyContent: 'center',
          }}
        >
          <Typography sx={{ fontSize: '0.75em' }}>{percent}%</Typography>
        </Box>
      </Box>
    </Grid>
  )
}

export default React.memo(ElevationFlag)
