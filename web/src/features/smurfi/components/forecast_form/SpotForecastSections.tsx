import React from 'react'
import { Controller, Control, FieldErrors } from 'react-hook-form'
import { Grid, Card, CardContent, Typography, TextField } from '@mui/material'
import type { FormData } from '@/features/smurfi/schemas/spotForecastSchema'

interface SpotForecastSectionsProps {
  control: Control<FormData>
  errors: FieldErrors<FormData>
  isMini: boolean
}

const SpotForecastSections: React.FC<SpotForecastSectionsProps> = ({ control, errors, isMini }) => {
  return (
    <>
      {/* ─── Inversion & Venting ─────────────────────────── */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Inversion & Venting
            </Typography>
            <Controller
              name="inversionVenting"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  multiline
                  rows={4}
                  fullWidth
                  error={!!errors.inversionVenting}
                  helperText={errors.inversionVenting?.message}
                />
              )}
            />
          </CardContent>
        </Card>
      </Grid>

      {/* ─── Outlook ─────────────────────────────────────── */}
      {!isMini && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Outlook (3-5 Day)
              </Typography>
              <Controller
                name="outlook"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    multiline
                    rows={4}
                    fullWidth
                    error={!!errors.outlook}
                    helperText={errors.outlook?.message}
                  />
                )}
              />
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* ─── Confidence/Discussion ───────────────────────── */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Confidence / Discussion
            </Typography>
            <Controller
              name="confidenceDiscussion"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  multiline
                  rows={4}
                  fullWidth
                  error={!!errors.confidenceDiscussion}
                  helperText={errors.confidenceDiscussion?.message}
                />
              )}
            />
          </CardContent>
        </Card>
      </Grid>
    </>
  )
}

export default SpotForecastSections
