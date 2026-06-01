import React from 'react'
import { Control, FieldErrors } from 'react-hook-form'
import { Grid, Card, CardContent, Typography } from '@mui/material'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import ControlledForecastTextField from '@/features/smurfi/components/forecastForm/ControlledForecastTextField'

interface SpotForecastSummariesProps {
  control: Control<SpotFormData>
  errors: FieldErrors<SpotFormData>
}

const parseOptionalNumber = (value: string) => (value === '' ? undefined : Number(value))

const SpotForecastSummaries: React.FC<SpotForecastSummariesProps> = ({ control, errors }) => {
  return (
    <Grid size={12}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Forecast Summaries
          </Typography>
          <Grid container spacing={2}>
            {/* Afternoon */}
            <Grid size={12}>
              <Typography variant="subtitle1" sx={{ paddingBottom: 1 }}>
                Afternoon
              </Typography>
              <Grid container spacing={1}>
                <Grid size={12} sx={{ paddingBottom: 1 }}>
                  <ControlledForecastTextField
                    name="afternoonForecast.description"
                    control={control}
                    label="Description"
                    fullWidth
                    multiline
                    rows={2}
                  />
                </Grid>
                <Grid size={12}>
                  <Grid container spacing={1}>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <ControlledForecastTextField
                        name="afternoonForecast.maxTemp"
                        control={control}
                        label="Max Temp (°C)"
                        type="number"
                        fullWidth
                        errorMessage={errors.afternoonForecast?.maxTemp?.message}
                        parseValue={parseOptionalNumber}
                      />
                    </Grid>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <ControlledForecastTextField
                        name="afternoonForecast.minRh"
                        control={control}
                        label="Min RH (%)"
                        type="number"
                        fullWidth
                        errorMessage={errors.afternoonForecast?.minRh?.message}
                        parseValue={parseOptionalNumber}
                      />
                    </Grid>
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
            {/* Tonight */}
            <Grid size={12}>
              <Typography variant="subtitle1" sx={{ paddingBottom: 1 }}>
                Tonight
              </Typography>
              <Grid container spacing={1}>
                <Grid size={12} sx={{ paddingBottom: 1 }}>
                  <ControlledForecastTextField
                    name="tonightForecast.description"
                    control={control}
                    label="Description"
                    fullWidth
                    multiline
                    rows={2}
                  />
                </Grid>
                <Grid size={12}>
                  <Grid container spacing={1}>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <ControlledForecastTextField
                        name="tonightForecast.minTemp"
                        control={control}
                        label="Min Temp (°C)"
                        type="number"
                        fullWidth
                        errorMessage={errors.tonightForecast?.minTemp?.message}
                        parseValue={parseOptionalNumber}
                      />
                    </Grid>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <ControlledForecastTextField
                        name="tonightForecast.maxRh"
                        control={control}
                        label="Max RH (%)"
                        type="number"
                        fullWidth
                        errorMessage={errors.tonightForecast?.maxRh?.message}
                        parseValue={parseOptionalNumber}
                      />
                    </Grid>
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
            {/* Tomorrow */}
            <Grid size={12}>
              <Typography variant="subtitle1" sx={{ paddingBottom: 1 }}>
                Tomorrow
              </Typography>
              <Grid container spacing={1}>
                <Grid size={12} sx={{ paddingBottom: 1 }}>
                  <ControlledForecastTextField
                    name="tomorrowForecast.description"
                    control={control}
                    label="Description"
                    fullWidth
                    multiline
                    rows={2}
                  />
                </Grid>
                <Grid size={12}>
                  <Grid container spacing={1}>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <ControlledForecastTextField
                        name="tomorrowForecast.maxTemp"
                        control={control}
                        label="Temp (°C)"
                        type="number"
                        fullWidth
                        errorMessage={errors.tomorrowForecast?.maxTemp?.message}
                        parseValue={parseOptionalNumber}
                      />
                    </Grid>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <ControlledForecastTextField
                        name="tomorrowForecast.minRh"
                        control={control}
                        label="Min RH (%)"
                        type="number"
                        fullWidth
                        errorMessage={errors.tomorrowForecast?.minRh?.message}
                        parseValue={parseOptionalNumber}
                      />
                    </Grid>
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Grid>
  )
}

export default SpotForecastSummaries
