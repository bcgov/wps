import { Card, CardContent, Grid, TextField, Typography } from '@mui/material'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import React from 'react'
import { Control, Controller, FieldErrors } from 'react-hook-form'

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
                slotProps={{
                  input: {
                    readOnly: true
                  }
                }}
              />
            )}
          />
        </CardContent>
      </Card>
    </Grid>
  )
}

export default SpotForecastSynopsis
