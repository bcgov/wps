import React from 'react'
import { Control, FieldErrors } from 'react-hook-form'
import { Card, CardContent, Grid, TextField } from '@mui/material'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import ControlledForecastTextField from '@/features/smurfi/components/forecastForm/ControlledForecastTextField'

interface SpotForecasterInfoProps {
  control: Control<SpotFormData>
  errors: FieldErrors<SpotFormData>
  forecasterName?: string
  forecasterEmail?: string
}

const SpotForecasterInfo: React.FC<SpotForecasterInfoProps> = ({
  control,
  errors,
  forecasterName,
  forecasterEmail
}) => (
  <Grid size={12}>
    <Card>
      <CardContent>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField label="Forecaster Name" value={forecasterName ?? ''} fullWidth disabled />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField label="Forecaster Email" value={forecasterEmail ?? ''} fullWidth disabled />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <ControlledForecastTextField
              name="forecasterPhone"
              control={control}
              label="Forecaster Phone"
              fullWidth
              errorMessage={errors.forecasterPhone?.message}
            />
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  </Grid>
)

export default SpotForecasterInfo
