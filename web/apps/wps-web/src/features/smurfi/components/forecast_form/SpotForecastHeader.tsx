import React from 'react'
import { Controller, Control, FieldErrors } from 'react-hook-form'
import { Grid, Card, CardContent, TextField, InputAdornment } from '@mui/material'
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon'
import { LocalizationProvider, DateTimePicker } from '@mui/x-date-pickers'
import StationSelector from '@/features/smurfi/components/StationSelector'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import { input } from '@testing-library/user-event/dist/cjs/event/input.js'

interface SpotForecastHeaderProps {
  control: Control<SpotFormData>
  errors: FieldErrors<SpotFormData>
  readOnly?: boolean
}

const SpotForecastHeader: React.FC<SpotForecastHeaderProps> = ({ control, errors, readOnly = false }) => {
  return (
    <LocalizationProvider dateAdapter={AdapterLuxon}>
      <Grid size={12}>
        <Card>
          <CardContent>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Controller
                  name="issuedDate"
                  control={control}
                  render={({ field }) => (
                    <DateTimePicker
                      label="Date/Time Issued"
                      value={field.value}
                      onChange={field.onChange}
                      timezone="America/Vancouver"
                      disabled={readOnly}
                      slotProps={{
                        textField: {
                          fullWidth: true,
                          error: !!errors.issuedDate,
                          helperText: errors.issuedDate?.message
                        }
                      }}
                    />
                  )}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Controller
                  name="expiryDate"
                  control={control}
                  render={({ field }) => (
                    <DateTimePicker
                      label="Expiry"
                      value={field.value}
                      onChange={field.onChange}
                      timezone="America/Vancouver"
                      disabled={readOnly}
                      slotProps={{
                        textField: {
                          fullWidth: true,
                          error: !!errors.expiryDate,
                          helperText: errors.expiryDate?.message
                        }
                      }}
                    />
                  )}
                />
              </Grid>

              <Grid size={{ xs: 12, sm: 6 }}>
                <Controller
                  name="fireProj"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Fire/Proj #"
                      fullWidth
                      error={!!errors.fireProj}
                      helperText={errors.fireProj?.message}
                      slotProps={{ input: { readOnly: true } }}
                    />
                  )}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Controller
                  name="requestBy"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Request by"
                      fullWidth
                      error={!!errors.requestBy}
                      helperText={errors.requestBy?.message}
                      disabled
                    />
                  )}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <Controller
                  name="forecastBy"
                  control={control}
                  render={({ field }) => <TextField {...field} label="Forecast by" fullWidth disabled />}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <Controller
                  name="email"
                  control={control}
                  render={({ field }) => (
                    <TextField {...field} label="Email" fullWidth slotProps={{ input: { readOnly: true } }} />
                  )}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <Controller
                  name="phone"
                  control={control}
                  render={({ field }) => (
                    <TextField {...field} label="Phone" fullWidth slotProps={{ input: { readOnly: true } }} />
                  )}
                />
              </Grid>

              {/* Location / Geometry fields */}
              <Grid size={{ xs: 12, sm: 6 }}>
                <Controller
                  name="city"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="City"
                      fullWidth
                      error={!!errors.city}
                      helperText={errors.city?.message}
                      slotProps={{ input: { readOnly: true } }}
                    />
                  )}
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
                <Controller
                  name="latitude"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Latitude"
                      fullWidth
                      error={!!errors.latitude}
                      helperText={errors.latitude?.message}
                      slotProps={{ input: { readOnly: true } }}
                    />
                  )}
                />
              </Grid>
              <Grid size={{ xs: 6, sm: 3 }}>
                <Controller
                  name="longitude"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Longitude"
                      fullWidth
                      error={!!errors.longitude}
                      helperText={errors.longitude?.message}
                      slotProps={{ input: { readOnly: true } }}
                    />
                  )}
                />
              </Grid>
              <Grid size={{ xs: 6, sm: 3 }}>
                <Controller
                  name="slopeAspect"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Slope/Aspect"
                      fullWidth
                      error={!!errors.slopeAspect}
                      helperText={errors.slopeAspect?.message}
                      slotProps={{ input: { readOnly: true } }}
                    />
                  )}
                />
              </Grid>
              <Grid size={{ xs: 6, sm: 3 }}>
                <Controller
                  name="valley"
                  control={control}
                  render={({ field }) => (
                    <TextField {...field} label="Valley" fullWidth slotProps={{ input: { readOnly: true } }} />
                  )}
                />
              </Grid>
              <Grid size={6}>
                <Controller
                  name="elevation"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Elevation"
                      fullWidth
                      slotProps={{
                        input: {
                          readOnly: true,
                          endAdornment: <InputAdornment position="end">m</InputAdornment>
                        }
                      }}
                    />
                  )}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Controller
                  name="size"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Size (ha)"
                      fullWidth
                      slotProps={{
                        input: {
                          readOnly: true,
                          endAdornment: <InputAdornment position="end">ha</InputAdornment>
                        }
                      }}
                    />
                  )}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </LocalizationProvider>
  )
}

export default SpotForecastHeader
