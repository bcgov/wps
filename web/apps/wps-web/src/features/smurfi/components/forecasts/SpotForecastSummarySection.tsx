import React from 'react'
import { Box, Typography } from '@mui/material'
import { SpotDescriptiveWeatherOutput } from '@wps/api/SMURFIAPI'

const ensurePeriod = (text: string | null): string => {
  if (!text) {
    return ''
  }
  return text.endsWith('.') ? text : `${text}.`
}

interface SpotForecastSummarySectionProps {
  descriptiveWeather: SpotDescriptiveWeatherOutput[]
}

const SpotForecastSummarySection: React.FC<SpotForecastSummarySectionProps> = ({ descriptiveWeather }) => {
  if (!descriptiveWeather || descriptiveWeather.length === 0) return null

  const afternoonForecast = descriptiveWeather.find(dw => dw.period === 'Today')
  const tonightForecast = descriptiveWeather.find(dw => dw.period === 'Tonight')
  const tomorrowForecast = descriptiveWeather.find(dw => dw.period === 'Tomorrow')

  return (
    <Box sx={{ mt: 1.5 }}>
      <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
        <strong>
          <span style={{ textDecoration: 'underline' }}>FORECAST:</span>
        </strong>
      </Typography>
      {afternoonForecast && (
        <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
          <strong>AFTERNOON:</strong>
          {'  '}
          {ensurePeriod(afternoonForecast.conditions)} MAX TEMP {afternoonForecast.temperature}C, MIN RH{' '}
          {afternoonForecast.relative_humidity}%
        </Typography>
      )}
      {tonightForecast && (
        <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
          <strong>TONIGHT:</strong>
          {'  '}
          {ensurePeriod(tonightForecast.conditions)} MIN TEMP {tonightForecast.temperature}C. MAX RH{' '}
          {tonightForecast.relative_humidity}%.
        </Typography>
      )}
      {tomorrowForecast && (
        <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
          <strong>TOMORROW:</strong>
          {'  '}
          {ensurePeriod(tomorrowForecast.conditions)} TEMP {tomorrowForecast.temperature}C. MIN RH{' '}
          {tomorrowForecast.relative_humidity}%.
        </Typography>
      )}
    </Box>
  )
}

export default SpotForecastSummarySection
