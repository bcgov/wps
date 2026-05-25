import React from 'react'
import { Box, Button, Divider, Paper, Typography } from '@mui/material'
import { DateTime } from 'luxon'
import { useNavigate } from 'react-router-dom'
import { SpotForecastOutput, SpotRequestOutput } from '@wps/api/SMURFIAPI'
import WeatherDataTable from '@/features/smurfi/components/forecasts/WeatherDataTable'
import { RepresentativeStation } from '@/features/smurfi/interfaces'
import { SMURFI_DASHBOARD_ROUTE } from '@wps/utils/constants'

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

export interface FullSpotForecastProps {
  forecast: SpotForecastOutput
  spotRequest: SpotRequestOutput
  representativeStations: RepresentativeStation[]
}

const FullSpotForecast: React.FC<FullSpotForecastProps> = ({ forecast, spotRequest, representativeStations }) => {
  const navigate = useNavigate()
  const afternoonForecast = forecast.descriptive_weather.find(dw => dw.period === 'Today')
  const tonightForecast = forecast.descriptive_weather.find(dw => dw.period === 'Tonight')
  const tomorrowForecast = forecast.descriptive_weather.find(dw => dw.period === 'Tomorrow')
  const stationsStr =
    representativeStations.length > 0
      ? representativeStations.map(s => `${s.name}${s.elevation != null ? ` (${s.elevation}m)` : ''}`).join(', ')
      : '—'

  const printableUrl = `${SMURFI_DASHBOARD_ROUTE}/${spotRequest.id}/forecasts/${forecast.id}/printable`

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box>
        <Button variant="outlined" size="small" onClick={() => navigate(printableUrl)}>
          Printable Version
        </Button>
      </Box>
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
        <Section title="Forecast Info">
          <Field label="Fire Number(s)" value={spotRequest.fire_number?.join(', ') ?? '—'} />
          <Field label="Requested By" value={spotRequest.requestor_name} />
          <Field label="Issued" value={formatDateTime(forecast.issued_at)} />
          <Field label="Expires" value={forecast.expires_at ? formatDateTime(forecast.expires_at) : '—'} />
          <Field label="Forecaster" value={forecast.forecaster_name} />
          <Field label="Email" value={forecast.forecaster_email} />
          {forecast.forecaster_phone && <Field label="Phone" value={forecast.forecaster_phone} />}
          {forecast.fire_size != null && <Field label="Fire Size" value={`${forecast.fire_size} ha`} />}
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
          <Field label="Elevation" value={spotRequest.elevation ? `${spotRequest.elevation} m` : '—'} />
          <Field label="Slope / Aspect" value={spotRequest.aspect ?? '—'} />
        </Section>
      </Box>

      {forecast.synopsis && <TextSection title="Synopsis">{forecast.synopsis}</TextSection>}

      {(afternoonForecast ?? tonightForecast ?? tomorrowForecast) && (
        <Section title="Forecast Summary" contentSx={{ gridTemplateColumns: '1fr' }}>
          {afternoonForecast && (
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                Afternoon
              </Typography>
              <Typography variant="body2">
                {afternoonForecast.conditions} Max Temp: {afternoonForecast.temperature ?? '—'}°C, Min RH:{' '}
                {afternoonForecast.relative_humidity ?? '—'}%
              </Typography>
            </Box>
          )}
          {tonightForecast && (
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                Tonight
              </Typography>
              <Typography variant="body2">
                {tonightForecast.conditions} Min Temp: {tonightForecast.temperature ?? '—'}°C, Max RH:{' '}
                {tonightForecast.relative_humidity ?? '—'}%
              </Typography>
            </Box>
          )}
          {tomorrowForecast && (
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                Tomorrow
              </Typography>
              <Typography variant="body2">
                {tomorrowForecast.conditions} Temp: {tomorrowForecast.temperature ?? '—'}°C, Min RH:{' '}
                {tomorrowForecast.relative_humidity ?? '—'}%
              </Typography>
            </Box>
          )}
        </Section>
      )}

      {forecast.tabular_weather.length > 0 && (
        <Paper variant="outlined" sx={{ p: 2.5 }}>
          <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: 1.5 }}>
            Weather Data
          </Typography>
          <Divider sx={{ mt: 0.5, mb: 2 }} />
          <WeatherDataTable rows={forecast.tabular_weather} issuedDate={forecast.issued_at} />
        </Paper>
      )}

      <Box
        sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: forecast.outlook ? '1fr 1fr' : '1fr' }, gap: 2 }}
      >
        {forecast.inversion_and_venting && (
          <TextSection title="Inversion & Venting">{forecast.inversion_and_venting}</TextSection>
        )}
        {forecast.outlook && <TextSection title="Outlook (3–5 Day)">{forecast.outlook}</TextSection>}
      </Box>

      {forecast.confidence && <TextSection title="Confidence / Discussion">{forecast.confidence}</TextSection>}
    </Box>
  )
}

export default FullSpotForecast
