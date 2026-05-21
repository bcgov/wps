import React from 'react'
import { Controller, Control, FieldErrors } from 'react-hook-form'
import { Grid, Card, CardContent, InputAdornment } from '@mui/material'
import StationSelector from '@/features/smurfi/components/StationSelector'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import ControlledForecastTextField from '@/features/smurfi/components/forecastForm/ControlledForecastTextField'
import ControlledForecastDateTimePicker from '@/features/smurfi/components/forecastForm/ControlledForecastDateTimePicker'

interface SpotForecastHeaderProps {
  control: Control<SpotFormData>
  errors: FieldErrors<SpotFormData>
}

const SpotForecastHeader: React.FC<SpotForecastHeaderProps> = ({ control, errors }) => {
  return (
    <Grid size={12}>
      <Card>
        <CardContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <ControlledForecastDateTimePicker
                name="issuedDate"
                control={control}
                label="Date/Time Issued"
                errorMessage={errors.issuedDate?.message}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <ControlledForecastDateTimePicker
                name="expiryDate"
                control={control}
                label="Expiry"
                errorMessage={errors.expiryDate?.message}
              />
            </Grid>

            <Grid size={{ xs: 12, sm: 6 }}>
              <ControlledForecastTextField
                name="fireProj"
                control={control}
                label="Fire/Proj #"
                fullWidth
                errorMessage={errors.fireProj?.message}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <ControlledForecastTextField
                name="requestBy"
                control={control}
                label="Request by"
                fullWidth
                errorMessage={errors.requestBy?.message}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Controller
                name="stns"
                control={control}
                render={({ field }) => <StationSelector value={field.value || []} onChange={field.onChange} />}
              />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <ControlledForecastTextField
                name="latitude"
                control={control}
                label="Latitude"
                fullWidth
                errorMessage={errors.latitude?.message}
              />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <ControlledForecastTextField
                name="longitude"
                control={control}
                label="Longitude"
                fullWidth
                errorMessage={errors.longitude?.message}
              />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <ControlledForecastTextField
                name="slopeAspect"
                control={control}
                label="Slope/Aspect"
                fullWidth
                errorMessage={errors.slopeAspect?.message}
              />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <ControlledForecastTextField name="valley" control={control} label="Valley" fullWidth />
            </Grid>
            <Grid size={6}>
              <ControlledForecastTextField
                name="elevation"
                control={control}
                label="Elevation"
                fullWidth
                endAdornment={<InputAdornment position="end">m</InputAdornment>}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <ControlledForecastTextField
                name="size"
                control={control}
                label="Size (ha)"
                fullWidth
                endAdornment={<InputAdornment position="end">ha</InputAdornment>}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Grid>
  )
}

export default SpotForecastHeader
