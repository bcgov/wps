import React from 'react'
import { Controller, Control } from 'react-hook-form'
import { Grid, Card, CardContent, Typography, TextField } from '@mui/material'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'

interface SpotForecastSummariesProps {
  control: Control<SpotFormData>
  readOnly?: boolean
}

const SpotForecastSummaries: React.FC<SpotForecastSummariesProps> = ({ control, readOnly = false }) => {
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
                  <Controller
                    name="afternoonForecast.description"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Description"
                        fullWidth
                        multiline
                        rows={2}
                        slotProps={{
                          input: { readOnly: true }
                        }}
                      />
                    )}
                  />
                </Grid>
                <Grid size={12}>
                  <Grid container spacing={1}>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <Controller
                        name="afternoonForecast.maxTemp"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Max Temp (°C)"
                            type="number"
                            fullWidth
                            slotProps={{
                              input: { readOnly: true }
                            }}
                            onChange={e => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                          />
                        )}
                      />
                    </Grid>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <Controller
                        name="afternoonForecast.minRh"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Min RH (%)"
                            type="number"
                            fullWidth
                            slotProps={{
                              input: { readOnly: true }
                            }}
                            onChange={e => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                          />
                        )}
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
                  <Controller
                    name="tonightForecast.description"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Description"
                        fullWidth
                        multiline
                        rows={2}
                        slotProps={{
                          input: { readOnly: true }
                        }}
                      />
                    )}
                  />
                </Grid>
                <Grid size={12}>
                  <Grid container spacing={1}>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <Controller
                        name="tonightForecast.minTemp"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Min Temp (°C)"
                            type="number"
                            fullWidth
                            slotProps={{
                              input: { readOnly: true }
                            }}
                            onChange={e => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                          />
                        )}
                      />
                    </Grid>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <Controller
                        name="tonightForecast.maxRh"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Max RH (%)"
                            type="number"
                            fullWidth
                            slotProps={{
                              input: { readOnly: true }
                            }}
                            onChange={e => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                          />
                        )}
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
                  <Controller
                    name="tomorrowForecast.description"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Description"
                        fullWidth
                        multiline
                        rows={2}
                        slotProps={{
                          input: { readOnly: true }
                        }}
                      />
                    )}
                  />
                </Grid>
                <Grid size={12}>
                  <Grid container spacing={1}>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <Controller
                        name="tomorrowForecast.maxTemp"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Temp (°C)"
                            type="number"
                            fullWidth
                            slotProps={{
                              input: { readOnly: true }
                            }}
                            onChange={e => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                          />
                        )}
                      />
                    </Grid>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <Controller
                        name="tomorrowForecast.minRh"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Min RH (%)"
                            type="number"
                            fullWidth
                            slotProps={{
                              input: { readOnly: true }
                            }}
                            onChange={e => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                          />
                        )}
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
