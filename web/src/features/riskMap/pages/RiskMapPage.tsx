import { FireMap } from '@/features/riskMap/pages/components/FireMap'
import { ImportButton } from '@/features/riskMap/pages/components/UploadButton'
import { Grid, Typography } from '@mui/material'
import { useState } from 'react'

export const RiskMapPage = () => {
  const [file, setFile] = useState<File | null>(null)
  return (
    <Grid
      container
      spacing={1}
      direction={'column'}
      justifyContent="center"
      alignItems="center"
      style={{ minHeight: '100vh' }}
    >
      <Grid item>
        <Typography variant="h5">Choose the values Shapefile to generate a risk map</Typography>
      </Grid>
      <Grid item>
        <ImportButton setFile={setFile} />
      </Grid>
      <Grid item>
        <FireMap file={file} />
      </Grid>
    </Grid>
  )
}
