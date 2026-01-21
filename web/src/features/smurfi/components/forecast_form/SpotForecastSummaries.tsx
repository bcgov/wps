import React from 'react'
import { Controller, Control } from 'react-hook-form'
import { Grid, Card, CardContent, Typography, TextField } from '@mui/material'
import type { FormData } from '@/features/smurfi/schemas/spotForecastSchema'

interface SpotForecastSummariesProps {
  control: Control<FormData>
}

const SpotForecastSummaries: React.FC<SpotForecastSummariesProps> = ({ control }) => {
  return (
    <Grid item xs={12}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Forecast Summaries
          </Typography>
          <Grid container spacing={2}>
            {/* Afternoon */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" paddingBottom={1}>
                Afternoon
              </Typography>
              <Grid container spacing={1}>
                <Grid item xs={12} paddingBottom={1}>
                  <Controller
                    name="afternoonForecast.description"
                    control={control}
                    render={({ field }) => <TextField {...field} label="Description" fullWidth multiline rows={2} />}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Grid container spacing={1}>
                    <Grid item xs={6} sm={3}>
                      <Controller
                        name="afternoonForecast.maxTemp"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Max Temp (°C)"
                            type="number"
                            fullWidth
                            onChange={e => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                          />
                        )}
                      />
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Controller
                        name="afternoonForecast.minRh"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Min RH (%)"
                            type="number"
                            fullWidth
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
            <Grid item xs={12}>
              <Typography variant="subtitle1" paddingBottom={1}>
                Tonight
              </Typography>
              <Grid container spacing={1}>
                <Grid item xs={12} paddingBottom={1}>
                  <Controller
                    name="tonightForecast.description"
                    control={control}
                    render={({ field }) => <TextField {...field} label="Description" fullWidth multiline rows={2} />}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Grid container spacing={1}>
                    <Grid item xs={6} sm={3}>
                      <Controller
                        name="tonightForecast.minTemp"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Min Temp (°C)"
                            type="number"
                            fullWidth
                            onChange={e => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                          />
                        )}
                      />
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Controller
                        name="tonightForecast.maxRh"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Max RH (%)"
                            type="number"
                            fullWidth
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
            <Grid item xs={12}>
              <Typography variant="subtitle1" paddingBottom={1}>
                Tomorrow
              </Typography>
              <Grid container spacing={1}>
                <Grid item xs={12} paddingBottom={1}>
                  <Controller
                    name="tomorrowForecast.description"
                    control={control}
                    render={({ field }) => <TextField {...field} label="Description" fullWidth multiline rows={2} />}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Grid container spacing={1}>
                    <Grid item xs={6} sm={3}>
                      <Controller
                        name="tomorrowForecast.maxTemp"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Temp (°C)"
                            type="number"
                            fullWidth
                            onChange={e => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                          />
                        )}
                      />
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Controller
                        name="tomorrowForecast.minRh"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Min RH (%)"
                            type="number"
                            fullWidth
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
