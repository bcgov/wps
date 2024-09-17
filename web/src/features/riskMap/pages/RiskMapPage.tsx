import { ImportButton } from '@/features/riskMap/pages/components/UploadButton'
import { Grid, Typography } from '@mui/material'

export const RiskMapPage = () => {
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
        <ImportButton />
      </Grid>
    </Grid>
  )
}
