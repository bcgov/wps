import React from 'react'
import { Grid, Typography } from '@mui/material'

interface ElevationLabelProps {
  label: string
}

const ElevationLabel = ({ label }: ElevationLabelProps) => {
  return (
    <Grid item sx={{ alignItems: 'center', display: 'flex', height: '25%', justifyContent: 'flex-end' }} xs={12}>
      <Typography sx={{ fontSize: '0.75em' }}>{label}</Typography>
    </Grid>
  )
}

export default React.memo(ElevationLabel)
