import React from 'react'
import { Box, Divider, Paper, Typography } from '@mui/material'
import { DateTime } from 'luxon'
import { SpotForecastOutput, SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { RepresentativeStation } from '@/features/smurfi/interfaces'
import WeatherDataTable from '@/features/smurfi/components/forecasts/WeatherDataTable'

const TIMEZONE = 'America/Vancouver'

const formatDateTime = (iso: string) => {
  const dt = DateTime.fromISO(iso).setZone(TIMEZONE)
  return dt.isValid ? `${dt.toFormat('HHmm')} ${dt.offsetNameShort} ${dt.toFormat('EEE, MMM d, yyyy')}` : iso
}

const Field = ({ label, value }: { label: string; value: React.ReactNode }) => (
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

const Section = ({ title, children, contentSx }: { title: string; children: React.ReactNode; contentSx?: object }) => (
  <Paper variant="outlined" sx={{ p: 2.5, display: 'flex', flexDirection: 'column' }}>
    <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: 1.5 }}>
      {title}
    </Typography>
    <Divider sx={{ mt: 0.5, mb: 2 }} />
    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, ...contentSx }}>{children}</Box>
  </Paper>
)

const TextSection = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <Paper variant="outlined" sx={{ p: 2.5 }}>
    <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: 1.5 }}>
      {title}
    </Typography>
    <Divider sx={{ mt: 0.5, mb: 2 }} />
    <Typography variant="body1">{children}</Typography>
  </Paper>
)

export interface MiniSpotForecastProps {
  forecast: SpotForecastOutput
  spotRequest: SpotRequestOutput
  representativeStations: RepresentativeStation[]
}

const MiniSpotForecast: React.FC<MiniSpotForecastProps> = ({ forecast, spotRequest, representativeStations }) => {
  const stationsStr =
    representativeStations.length > 0
      ? representativeStations.map(s => s.name + (s.elevation == null ? '' : ` (${s.elevation}m)`)).join(', ')
      : '—'

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
        <Section title="Forecast Info">
          <Field label="Fire Number(s)" value={spotRequest.fire_number?.join(', ') ?? '—'} />
          <Field label="Requested By" value={spotRequest.requestor_name} />
          <Field label="Issued" value={formatDateTime(forecast.issued_at)} />
          <Field label="Expires" value={forecast.expires_at ? formatDateTime(forecast.expires_at) : '—'} />
          <Field label="Forecaster" value={forecast.forecaster_name} />
          <Field label="Email" value={forecast.forecaster_email} />
          {forecast.forecaster_phone && <Field label="Phone" value={forecast.forecaster_phone} />}
          <Box sx={{ gridColumn: '1 / -1' }}>
            <Field label="Representative Stations" value={stationsStr} />
          </Box>
        </Section>

        <Section title="Location">
          <Box sx={{ gridColumn: '1 / -1' }}>
            <Field label="Geographic Description" value={spotRequest.geographic_description} />
          </Box>
          <Field label="Latitude" value={spotRequest.latitude.toFixed(4)} />
          <Field label="Longitude" value={spotRequest.longitude.toFixed(4)} />
        </Section>
      </Box>

      {forecast.tabular_weather.length > 0 && (
        <Paper variant="outlined" sx={{ p: 2.5 }}>
          <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: 1.5 }}>
            Weather Data
          </Typography>
          <Divider sx={{ mt: 0.5, mb: 2 }} />
          <WeatherDataTable rows={forecast.tabular_weather} issuedDate={forecast.issued_at} />
        </Paper>
      )}

      {forecast.synopsis && <TextSection title="Notes / Discussion">{forecast.synopsis}</TextSection>}

      {forecast.inversion_and_venting && (
        <TextSection title="Venting / Inversions">{forecast.inversion_and_venting}</TextSection>
      )}

      {forecast.confidence && (
        <TextSection title="Long Range Model Guidance and Discussion">{forecast.confidence}</TextSection>
      )}
    </Box>
  )
}

export default MiniSpotForecast
