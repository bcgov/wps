import React from 'react'
import { Box, Typography } from '@mui/material'
import { SpotForecastOutput, SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { RepresentativeStation } from '@/features/smurfi/interfaces'
import {
  Field,
  Section,
  TextSection,
  WeatherDataSection
} from '@/features/smurfi/components/forecasts/SpotForecastComponents'
import { formatDateTime, formatStationsStr } from '@/features/smurfi/utils/spotForecastUtils'

const formatFireSizes = (fireSizes: (number | null)[] | null | undefined) =>
  fireSizes?.some(fireSize => fireSize !== null)
    ? fireSizes.map(fireSize => (fireSize === null ? '—' : `${fireSize} ha`)).join(', ')
    : null

export interface FullSpotForecastProps {
  forecast: SpotForecastOutput
  spotRequest: SpotRequestOutput
  representativeStations: RepresentativeStation[]
}

const FullSpotForecast: React.FC<FullSpotForecastProps> = ({ forecast, spotRequest, representativeStations }) => {
  const afternoonForecast = forecast.descriptive_weather.find(dw => dw.period === 'Today')
  const tonightForecast = forecast.descriptive_weather.find(dw => dw.period === 'Tonight')
  const tomorrowForecast = forecast.descriptive_weather.find(dw => dw.period === 'Tomorrow')
  const stationsStr = formatStationsStr(representativeStations)

  const forecastInstance = forecast.spot_request_instance

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
          {forecast.fire_size != null && <Field label="Fire Size(s)" value={formatFireSizes(forecast.fire_size)} />}
          <Box sx={{ gridColumn: '1 / -1' }}>
            <Field label="Representative Stations" value={stationsStr} />
          </Box>
        </Section>

        <Section title="Location">
          <Box sx={{ gridColumn: '1 / -1' }}>
            <Field label="Geographic Description" value={forecastInstance.geographic_description} />
          </Box>
          <Field label="Latitude" value={forecastInstance.latitude.toFixed(4)} />
          <Field label="Longitude" value={forecastInstance.longitude.toFixed(4)} />
          <Field label="Elevation" value={forecastInstance.elevation ? `${forecastInstance.elevation} m` : '—'} />
          <Field label="Slope / Aspect" value={forecastInstance.aspect ?? '—'} />
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
                {`${afternoonForecast.conditions} Max Temp: ${afternoonForecast.temperature ?? '—'}°C, Min RH: ${afternoonForecast.relative_humidity ?? '—'}%`}
              </Typography>
            </Box>
          )}
          {tonightForecast && (
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                Tonight
              </Typography>
              <Typography variant="body2">
                {`${tonightForecast.conditions} Min Temp: ${tonightForecast.temperature ?? '—'}°C, Max RH: ${tonightForecast.relative_humidity ?? '—'}%`}
              </Typography>
            </Box>
          )}
          {tomorrowForecast && (
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                Tomorrow
              </Typography>
              <Typography variant="body2">
                {`${tomorrowForecast.conditions} Temp: ${tomorrowForecast.temperature ?? '—'}°C, Min RH: ${tomorrowForecast.relative_humidity ?? '—'}%`}
              </Typography>
            </Box>
          )}
        </Section>
      )}

      <WeatherDataSection forecast={forecast} />

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
