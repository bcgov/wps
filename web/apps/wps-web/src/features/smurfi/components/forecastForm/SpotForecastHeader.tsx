import React from 'react'
import { Controller, Control, FieldErrors, UseFormSetValue, useWatch } from 'react-hook-form'
import { Grid, Card, CardContent, InputAdornment, Typography } from '@mui/material'
import StationSelector from '@/features/smurfi/components/StationSelector'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import ControlledForecastTextField from '@/features/smurfi/components/forecastForm/ControlledForecastTextField'
import ControlledForecastDateTimePicker from '@/features/smurfi/components/forecastForm/ControlledForecastDateTimePicker'
import SpotRequestLocationMap from '@/features/smurfi/components/requestForm/SpotRequestLocationMap'
import { SpotRequestOutput } from '@wps/api/SMURFIAPI'

interface SpotForecastHeaderProps {
  control: Control<SpotFormData>
  errors: FieldErrors<SpotFormData>
  fireNumbers: string[] | null | undefined
  spotRequest: SpotRequestOutput
  setValue: UseFormSetValue<SpotFormData>
}

const toNumericLocation = (latitude: string | undefined, longitude: string | undefined) => {
  const lat = Number(latitude)
  const lon = Number(longitude)
  return Number.isFinite(lat) && Number.isFinite(lon) ? { latitude: lat, longitude: lon } : null
}

const getFireSizeErrorMessage = (errors: FieldErrors<SpotFormData>, index: number) => {
  const fireSizesError = errors.fireSizes
  return Array.isArray(fireSizesError) ? fireSizesError[index]?.message : undefined
}

const SpotForecastHeader: React.FC<SpotForecastHeaderProps> = ({
  control,
  errors,
  fireNumbers,
  spotRequest,
  setValue
}) => {
  const latitude = useWatch({ control, name: 'latitude' })
  const longitude = useWatch({ control, name: 'longitude' })
  const selectedLocation = toNumericLocation(latitude, longitude)
  const fireSizeLabels = fireNumbers?.length ? fireNumbers : ['Fire Size']

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
                label="Fire/Proj #s"
                fullWidth
                disabled
                errorMessage={errors.fireProj?.message}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <ControlledForecastTextField
                name="requestBy"
                control={control}
                label="Request by"
                fullWidth
                disabled
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
            <Grid size={12}>
              <SpotRequestLocationMap
                value={selectedLocation}
                existingSpotRequests={[spotRequest]}
                focusOnValue
                onChange={location => {
                  if (!location) {
                    return
                  }
                  setValue('latitude', location.latitude.toFixed(6), { shouldValidate: true, shouldDirty: true })
                  setValue('longitude', location.longitude.toFixed(6), { shouldValidate: true, shouldDirty: true })
                }}
              />
            </Grid>
            <Grid size={12}>
              <ControlledForecastTextField
                name="geographicDescription"
                control={control}
                label="Geographic Description"
                fullWidth
                errorMessage={errors.geographicDescription?.message}
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
            <Grid size={12}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Fire Size(s)
              </Typography>
              <Grid container spacing={2}>
                {fireSizeLabels.map((fireNumber, index) => (
                  <Grid key={`${fireNumber}-${index}`} size={{ xs: 12, sm: 6 }}>
                    <ControlledForecastTextField
                      name={`fireSizes.${index}`}
                      control={control}
                      label={`${fireNumber} Size`}
                      fullWidth
                      errorMessage={getFireSizeErrorMessage(errors, index)}
                      endAdornment={<InputAdornment position="end">ha</InputAdornment>}
                    />
                  </Grid>
                ))}
              </Grid>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Grid>
  )
}

export default SpotForecastHeader
