import React from 'react'
import { Box, Divider, Paper, Typography } from '@mui/material'
import WeatherDataTable from '@/features/smurfi/components/forecasts/WeatherDataTable'
import { SpotForecastOutput } from '@wps/api/SMURFIAPI'

export const Field = ({ label, value }: { label: string; value: React.ReactNode }) => (
  <Box>
    <Typography
      variant="caption"
      color="text.secondary"
      sx={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.8 }}
    >
      {label}
    </Typography>
    <Typography variant="body1">{value ?? '—'}</Typography>
  </Box>
)

export const Section = ({
  title,
  children,
  contentSx
}: {
  title: string
  children: React.ReactNode
  contentSx?: object
}) => (
  <Paper variant="outlined" sx={{ p: 2.5, display: 'flex', flexDirection: 'column' }}>
    <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: 1.5 }}>
      {title}
    </Typography>
    <Divider sx={{ mt: 0.5, mb: 2 }} />
    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, ...contentSx }}>{children}</Box>
  </Paper>
)

export const TextSection = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <Paper variant="outlined" sx={{ p: 2.5 }}>
    <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: 1.5 }}>
      {title}
    </Typography>
    <Divider sx={{ mt: 0.5, mb: 2 }} />
    <Typography variant="body1">{children}</Typography>
  </Paper>
)

export const WeatherDataSection = ({ forecast }: { forecast: SpotForecastOutput }) => {
  if (forecast.tabular_weather.length === 0) return null
  return (
    <Paper variant="outlined" sx={{ p: 2.5 }}>
      <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: 1.5 }}>
        Weather Data
      </Typography>
      <Divider sx={{ mt: 0.5, mb: 2 }} />
      <WeatherDataTable rows={forecast.tabular_weather} issuedDate={forecast.issued_at} />
    </Paper>
  )
}
