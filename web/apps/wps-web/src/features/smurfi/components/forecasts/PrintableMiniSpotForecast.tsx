import React from 'react'
import { Box, Typography } from '@mui/material'
import { DateTime } from 'luxon'
import { SpotForecastOutput, SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { RepresentativeStation } from '@/features/smurfi/interfaces'
import WeatherDataTable from '@/features/smurfi/components/forecasts/WeatherDataTable'

const TIMEZONE = 'America/Vancouver'
const FONT_SIZE = '12px'

const ordinal = (n: number): string => {
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return n + (s[(v - 20) % 10] ?? s[v] ?? s[0])
}

export interface PrintableMiniSpotForecastProps {
  forecast: SpotForecastOutput
  spotRequest: SpotRequestOutput
  representativeStations: RepresentativeStation[]
}

const PrintableMiniSpotForecast: React.FC<PrintableMiniSpotForecastProps> = ({
  forecast,
  spotRequest,
  representativeStations
}) => {
  const issuedDt = DateTime.fromISO(forecast.issued_at).setZone(TIMEZONE)
  const fireNumberStr = spotRequest.fire_number?.join(', ') ?? ''
  const title = [fireNumberStr, 'Mini Spot Forecast'].filter(Boolean).join(' ')
  const issuedDateStr = `${issuedDt.toFormat('EEEE, MMMM ')}${ordinal(issuedDt.day)}${issuedDt.toFormat(', yyyy')}`
  const stationsStr = representativeStations
    .map(s => s.name + (s.elevation == null ? '' : ` (${s.elevation} m)`))
    .join(', ')

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h6" sx={{ fontWeight: 'bold', textAlign: 'center' }}>
        {title}
      </Typography>
      <Typography sx={{ fontSize: FONT_SIZE, textAlign: 'center', mb: 3 }}>{issuedDateStr}</Typography>

      <Typography sx={{ fontSize: FONT_SIZE, fontWeight: 'bold', lineHeight: 1.4 }}>
        {spotRequest.geographic_description}
      </Typography>
      <Typography sx={{ fontSize: FONT_SIZE, fontWeight: 'bold', mb: 2 }}>
        <span style={{ textDecoration: 'underline' }}>Lat/Long:</span>{' '}
        {spotRequest.latitude.toFixed(4)}, {spotRequest.longitude.toFixed(4)}
      </Typography>

      {stationsStr && (
        <Typography sx={{ fontSize: FONT_SIZE, mb: 3 }}>
          <strong style={{ textDecoration: 'underline' }}>Rep. Wx Station</strong>: {stationsStr}
        </Typography>
      )}

      <WeatherDataTable rows={forecast.tabular_weather} issuedDate={forecast.issued_at} fontSize={FONT_SIZE} />

      {forecast.synopsis && (
        <Box sx={{ mt: 3 }}>
          <Typography sx={{ fontSize: FONT_SIZE, fontWeight: 'bold', textDecoration: 'underline' }}>
            Notes/Discussion:
          </Typography>
          <Typography sx={{ fontSize: FONT_SIZE }}>{forecast.synopsis}</Typography>
        </Box>
      )}

      {forecast.inversion_and_venting && (
        <Box sx={{ mt: 2 }}>
          <Typography sx={{ fontSize: FONT_SIZE, fontWeight: 'bold', textDecoration: 'underline' }}>
            Venting/Inversions:
          </Typography>
          <Typography sx={{ fontSize: FONT_SIZE, mt: 1 }}>{forecast.inversion_and_venting}</Typography>
        </Box>
      )}

      {forecast.confidence && (
        <Box sx={{ mt: 2 }}>
          <Typography sx={{ fontSize: FONT_SIZE, fontWeight: 'bold', textDecoration: 'underline' }}>
            Long range model guidance and discussion:
          </Typography>
          <Typography sx={{ fontSize: FONT_SIZE, mt: 1 }}>{forecast.confidence}</Typography>
        </Box>
      )}

      <Box sx={{ mt: 4 }}>
        <Typography sx={{ fontSize: FONT_SIZE }}>{forecast.forecaster_name}</Typography>
        {forecast.forecaster_phone && <Typography sx={{ fontSize: FONT_SIZE }}>{forecast.forecaster_phone}</Typography>}
        <Typography sx={{ fontSize: FONT_SIZE }}>{forecast.forecaster_email}</Typography>
      </Box>
    </Box>
  )
}

export default PrintableMiniSpotForecast
