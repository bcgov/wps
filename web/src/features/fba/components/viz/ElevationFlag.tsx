import React from 'react'
import { Box, Grid, Typography } from '@mui/material'

export enum HFIRiskStatus {
  ADVISORY = 'Advisory',
  LOW = 'Low',
  WARNING = 'Warning'
}

const ElevationRiskStatus = {
  Low: {
    color: '#CCCCCC',
    label: HFIRiskStatus.LOW
  },
  Advisory: {
    color: '#FFD2AB',
    label: HFIRiskStatus.ADVISORY
  },
  Warning: {
    color: '#CDA3A4',
    label: HFIRiskStatus.WARNING
  }
}

interface ElevationFlagProps {
  status: HFIRiskStatus
}

const ElevationFlag = ({ status }: ElevationFlagProps) => {
  return (
    <Grid sx={{ display: 'flex', alignItems: 'center', flexGrow: 1, justifyContent: 'flex-start' }} xs={12}>
      <Box
        sx={{
          alignItems: 'center',
          backgroundColor: ElevationRiskStatus[status].color,
          clipPath: 'polygon(0 50%, 10% 0, 100% 0, 100% 100%, 10% 100%)',
          display: 'flex',
          height: '32px',
          justifyContent: 'center',
          width: '100px'
        }}
      >
        <Typography sx={{ color: '#003466', fontSize: '0.75em' }}>{ElevationRiskStatus[status].label}</Typography>
      </Box>
    </Grid>
  )
}

export default React.memo(ElevationFlag)
