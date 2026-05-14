import React from 'react'
import { Controller, Control, FieldErrors } from 'react-hook-form'
import { Grid, Card, CardContent, Typography, TextField } from '@mui/material'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'

interface SpotForecastSectionsProps {
  control: Control<SpotFormData>
  errors: FieldErrors<SpotFormData>
  isMini: boolean
  readOnly?: boolean
}

const SpotForecastSections: React.FC<SpotForecastSectionsProps> = ({ control, errors, isMini, readOnly = false }) => {
  return (
    <>
      {/* ─── Inversion & Venting ─────────────────────────── */}
      <Grid size={12}>
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
                  slotProps={{
                    input: {
                      readOnly: true
                    }
                  }}
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
        <Grid size={12}>
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
                    slotProps={{
                      input: {
                        readOnly: true
                      }
                    }}
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
      <Grid size={12}>
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
                  slotProps={{
                    input: {
                      readOnly: true
                    }
                  }}
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
