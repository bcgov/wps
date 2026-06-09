import React from 'react'
import { Control, FieldErrors } from 'react-hook-form'
import { Grid, Card, CardContent, Typography } from '@mui/material'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import ControlledForecastTextField from '@/features/smurfi/components/forecastForm/ControlledForecastTextField'

interface SpotForecastSectionsProps {
  control: Control<SpotFormData>
  errors: FieldErrors<SpotFormData>
  isMini: boolean
}

const SpotForecastSections: React.FC<SpotForecastSectionsProps> = ({ control, errors, isMini }) => {
  return (
    <>
      {/* ─── Inversion & Venting ─────────────────────────── */}
      <Grid size={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Inversion & Venting
            </Typography>
            <ControlledForecastTextField
              name="inversionVenting"
              control={control}
              multiline
              rows={4}
              fullWidth
              errorMessage={errors.inversionVenting?.message}
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
              <ControlledForecastTextField
                name="outlook"
                control={control}
                multiline
                rows={4}
                fullWidth
                errorMessage={errors.outlook?.message}
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
            <ControlledForecastTextField
              name="confidenceDiscussion"
              control={control}
              multiline
              rows={4}
              fullWidth
              errorMessage={errors.confidenceDiscussion?.message}
            />
          </CardContent>
        </Card>
      </Grid>
    </>
  )
}

export default SpotForecastSections
