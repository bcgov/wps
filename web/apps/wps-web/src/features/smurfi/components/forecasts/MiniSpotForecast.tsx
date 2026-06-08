import React from 'react'
import { Box } from '@mui/material'
import { SpotForecastOutput, SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { RepresentativeStation } from '@/features/smurfi/interfaces'
import {
  Field,
  Section,
  TextSection,
  WeatherDataSection
} from '@/features/smurfi/components/forecasts/SpotForecastComponents'
import { formatDateTime, formatStationsStr } from '@/features/smurfi/utils/spotForecastUtils'

export interface MiniSpotForecastProps {
  forecast: SpotForecastOutput
  spotRequest: SpotRequestOutput
  representativeStations: RepresentativeStation[]
  locationMap?: React.ReactNode
}

const MiniSpotForecast: React.FC<MiniSpotForecastProps> = ({
  forecast,
  spotRequest,
  representativeStations,
  locationMap
}) => {
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
          <Field label="Phone" value={forecast.forecaster_phone ?? '—'} />
          <Box sx={{ gridColumn: '1 / -1' }}>
            <Field label="Representative Stations" value={stationsStr} />
          </Box>
        </Section>

        <Section
          title="Location"
          contentSx={{
            gridTemplateColumns: { xs: '1fr', lg: locationMap ? 'minmax(0, 0.9fr) minmax(280px, 1.1fr)' : '1fr 1fr' }
          }}
        >
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, alignContent: 'start' }}>
            <Box sx={{ gridColumn: '1 / -1' }}>
              <Field label="Geographic Description" value={forecastInstance.geographic_description} />
            </Box>
            <Field label="Latitude" value={forecastInstance.latitude.toFixed(4)} />
            <Field label="Longitude" value={forecastInstance.longitude.toFixed(4)} />
          </Box>
          {locationMap}
        </Section>
      </Box>

      <WeatherDataSection forecast={forecast} />

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
