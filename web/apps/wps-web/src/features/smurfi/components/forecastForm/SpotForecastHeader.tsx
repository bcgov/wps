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
  readOnly?: boolean
}

const SpotForecastHeader: React.FC<SpotForecastHeaderProps> = ({ control, errors, readOnly = false }) => {
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
                disabled={readOnly}
                errorMessage={errors.issuedDate?.message}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <ControlledForecastDateTimePicker
                name="expiryDate"
                control={control}
                label="Expiry"
                disabled={readOnly}
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
                readOnly={readOnly}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <ControlledForecastTextField
                name="requestBy"
                control={control}
                label="Request by"
                fullWidth
                errorMessage={errors.requestBy?.message}
                readOnly={readOnly}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <ControlledForecastTextField
                name="forecastBy"
                control={control}
                label="Forecast by"
                fullWidth
                errorMessage={errors.forecastBy?.message}
                readOnly={readOnly}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <ControlledForecastTextField
                name="email"
                control={control}
                label="Email"
                fullWidth
                errorMessage={errors.email?.message}
                readOnly={readOnly}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <ControlledForecastTextField
                name="phone"
                control={control}
                label="Phone"
                fullWidth
                errorMessage={errors.phone?.message}
                readOnly={readOnly}
              />
            </Grid>

            {/* Location / Geometry fields */}
            <Grid size={{ xs: 12, sm: 6 }}>
              <ControlledForecastTextField
                name="city"
                control={control}
                label="City"
                fullWidth
                errorMessage={errors.city?.message}
                readOnly={readOnly}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Controller
                name="stns"
                control={control}
                render={({ field }) => (
                  <StationSelector value={field.value || []} onChange={readOnly ? () => {} : field.onChange} />
                )}
              />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <ControlledForecastTextField
                name="latitude"
                control={control}
                label="Latitude"
                fullWidth
                errorMessage={errors.latitude?.message}
                readOnly={readOnly}
              />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <ControlledForecastTextField
                name="longitude"
                control={control}
                label="Longitude"
                fullWidth
                errorMessage={errors.longitude?.message}
                readOnly={readOnly}
              />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <ControlledForecastTextField
                name="slopeAspect"
                control={control}
                label="Slope/Aspect"
                fullWidth
                errorMessage={errors.slopeAspect?.message}
                readOnly={readOnly}
              />
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <ControlledForecastTextField
                name="valley"
                control={control}
                label="Valley"
                fullWidth
                readOnly={readOnly}
              />
            </Grid>
            <Grid size={6}>
              <ControlledForecastTextField
                name="elevation"
                control={control}
                label="Elevation"
                fullWidth
                readOnly={readOnly}
                endAdornment={<InputAdornment position="end">m</InputAdornment>}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <ControlledForecastTextField
                name="size"
                control={control}
                label="Size (ha)"
                fullWidth
                readOnly={readOnly}
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
