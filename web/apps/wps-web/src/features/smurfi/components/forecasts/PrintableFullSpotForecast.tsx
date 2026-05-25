import React from 'react'
import { Box, Container, Typography } from '@mui/material'
import { SpotForecastOutput, SpotRequestOutput } from '@wps/api/SMURFIAPI'
import SpotForecastHeaderTable from '@/features/smurfi/components/forecasts/SpotForecastHeaderTable'
import WeatherDataTable from '@/features/smurfi/components/forecasts/WeatherDataTable'
import SpotForecastSummarySection from '@/features/smurfi/components/forecasts/SpotForecastSummarySection'
import { RepresentativeStation } from '@/features/smurfi/interfaces'

interface PrintableFullSpotForecastProps {
  forecast: SpotForecastOutput
  spotRequest: SpotRequestOutput
  representativeStations: RepresentativeStation[]
}

const PrintableFullSpotForecast: React.FC<PrintableFullSpotForecastProps> = ({
  forecast,
  spotRequest,
  representativeStations
}) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
      <Container maxWidth="lg">
        <Typography variant="h5" sx={{ fontWeight: 'bold', textDecoration: 'underline', textAlign: 'center' }}>
          BC Wild Fire Service Spot Forecast
        </Typography>
        <SpotForecastHeaderTable
          forecast={forecast}
          spotRequest={spotRequest}
          representativeStations={representativeStations}
        />

        <Typography variant="body2" sx={{ mt: 1.5, lineHeight: 1.6 }}>
          <strong>
            <span style={{ textDecoration: 'underline' }}>SYNOPSIS:</span>
          </strong>
          {'  '}
          {forecast.synopsis}
        </Typography>

        <SpotForecastSummarySection descriptiveWeather={forecast.descriptive_weather} />

        <WeatherDataTable rows={forecast.tabular_weather} issuedDate={forecast.issued_at} />

        <Typography variant="body2" sx={{ mt: 2, lineHeight: 1.6 }}>
          <strong>
            <span style={{ textDecoration: 'underline' }}>INVERSION &amp; VENTING:</span>
          </strong>
          {'    '}
          {forecast.inversion_and_venting}
        </Typography>

        {forecast.outlook && (
          <Typography variant="body2" sx={{ mt: 2, lineHeight: 1.6 }}>
            <strong>
              <span style={{ textDecoration: 'underline' }}>OUTLOOK (3-5 Day Outlook</span>
            </strong>{' '}
            {forecast.outlook}
          </Typography>
        )}

        <Typography variant="body2" sx={{ mt: 2, lineHeight: 1.6 }}>
          <strong>
            <span style={{ textDecoration: 'underline' }}>CONFIDENCE/DISCUSSION:</span>
          </strong>
          {'  '}
          {forecast.confidence}
        </Typography>
      </Container>
    </Box>
  )
}

export default PrintableFullSpotForecast
