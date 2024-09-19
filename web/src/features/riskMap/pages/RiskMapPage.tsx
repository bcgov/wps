import { FireMap } from '@/features/riskMap/pages/components/FireMap'
import { ValuesImportButton } from '@/features/riskMap/pages/components/UploadButton'
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
        <Typography variant="h5">Choose the values GeoJSON file to generate a risk map</Typography>
      </Grid>
      <Grid item>
        <ValuesImportButton setFile={setFile} />
      </Grid>
      <Grid item>
        <FireMap valuesFile={file} />
      </Grid>
    </Grid>
  )
}
