import React from 'react'
import { Grid, Typography } from '@mui/material'

interface ElevationLabelProps {
  label: string
}

const ElevationLabel = ({ label }: ElevationLabelProps) => {
  return (
    <Grid item sx={{ alignItems: 'center', display: 'flex', justifyContent: 'flex-start' }} xs={6}>
      <Typography sx={{ fontWeight: 'bold' }}>{label}</Typography>
    </Grid>
  )
}

export default React.memo(ElevationLabel)
