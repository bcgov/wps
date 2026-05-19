import { Card, CardContent, Grid, Typography } from '@mui/material'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import React from 'react'
import { Control, FieldErrors } from 'react-hook-form'
import ControlledForecastTextField from '@/features/smurfi/components/forecastForm/ControlledForecastTextField'

interface SpotForecastSynopsisProps {
  control: Control<SpotFormData>
  errors: FieldErrors<SpotFormData>
  readOnly?: boolean
}

const SpotForecastSynopsis: React.FC<SpotForecastSynopsisProps> = ({ control, errors, readOnly = false }) => {
  return (
    <Grid size={12}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Synopsis
          </Typography>
          <ControlledForecastTextField
            name="synopsis"
            control={control}
            multiline
            rows={5}
            fullWidth
            errorMessage={errors.synopsis?.message}
            readOnly={readOnly}
          />
        </CardContent>
      </Card>
    </Grid>
  )
}

export default SpotForecastSynopsis
