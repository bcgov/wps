import React from 'react'
import { Controller, Control, FieldErrors } from 'react-hook-form'
import { Grid, Card, CardContent, Typography, TextField } from '@mui/material'
import type { FormData } from '@/features/smurfi/schemas/spotForecastSchema'

interface SpotForecastSynopsisProps {
  control: Control<FormData>
  errors: FieldErrors<FormData>
  readOnly?: boolean
}

const SpotForecastSynopsis: React.FC<SpotForecastSynopsisProps> = ({ control, errors, readOnly = false }) => {
  return (
    <Grid item xs={12}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Synopsis
          </Typography>
          <Controller
            name="synopsis"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                multiline
                rows={5}
                fullWidth
                error={!!errors.synopsis}
                helperText={errors.synopsis?.message}
                InputProps={{ readOnly }}
              />
            )}
          />
        </CardContent>
      </Card>
    </Grid>
  )
}

export default SpotForecastSynopsis
