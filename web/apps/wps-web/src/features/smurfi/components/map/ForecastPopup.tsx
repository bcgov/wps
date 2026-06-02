import React from 'react'
import { Box, Button, Typography } from '@mui/material'
import { ForecastPopupData } from '@/features/smurfi/interfaces'
import { formatDateTime } from '@/features/smurfi/utils/spotForecastUtils'

interface ForecastPopupProps {
  popupData: ForecastPopupData
  canSubmitForecast: boolean
  onOpenRequest: (spotId: number) => void
  onOpenForecast: (spotId: number, forecastId: number) => void
  onSubmitForecast: (spotId: number, sourceForecastId: number) => void
}

const ForecastPopup: React.FC<ForecastPopupProps> = ({
  popupData,
  canSubmitForecast,
  onOpenRequest,
  onOpenForecast,
  onSubmitForecast
}) => {
  const { lat, lng, fireNumber, spotId, forecastCount, latestForecast } = popupData
  const hasMultipleForecasts = forecastCount > 1

  const handleRequestClick = (event: React.MouseEvent) => {
    event.stopPropagation()
    event.preventDefault()
    onOpenRequest(spotId)
  }

  const handleForecastClick = (event: React.MouseEvent) => {
    event.stopPropagation()
    event.preventDefault()
    onOpenForecast(spotId, latestForecast.id)
  }

  const handleSubmitForecastClick = (event: React.MouseEvent) => {
    event.stopPropagation()
    event.preventDefault()
    onSubmitForecast(spotId, latestForecast.id)
  }

  return (
    <Box
      sx={{
        p: 2,
        background: 'white',
        border: '1px solid #ddd',
        borderRadius: 2,
        boxShadow: 3,
        minWidth: 340,
        maxWidth: 350
      }}
    >
      <Box sx={{ mb: 2 }}>
        <Typography variant="body2">{fireNumber}</Typography>
        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>
          Forecast location
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          Lat: {lat.toFixed(6)}, Lng: {lng.toFixed(6)}
        </Typography>
      </Box>

      <Box sx={{ mb: 2 }}>
        {hasMultipleForecasts && <Typography variant="body2">{forecastCount} forecasts at this location</Typography>}
        <Typography variant="body2">
          {hasMultipleForecasts ? 'Latest issued' : 'Issued'}: {formatDateTime(latestForecast.issued_at)}
        </Typography>
        <Typography variant="body2">Type: {latestForecast.forecast_type}</Typography>
        {latestForecast.forecaster_name && (
          <Typography variant="body2">Forecaster: {latestForecast.forecaster_name}</Typography>
        )}
      </Box>

      <Box sx={{ display: 'flex', gap: 1 }}>
        <Button variant="outlined" color="primary" size="small" fullWidth onClick={handleRequestClick}>
          View Request
        </Button>
        <Button variant="contained" color="primary" size="small" fullWidth onClick={handleForecastClick}>
          {hasMultipleForecasts ? 'View Latest Forecast' : 'View Forecast'}
        </Button>
      </Box>
      {canSubmitForecast && (
        <Button
          variant="outlined"
          color="primary"
          size="small"
          fullWidth
          onClick={handleSubmitForecastClick}
          sx={{ mt: 1 }}
        >
          New Forecast
        </Button>
      )}
    </Box>
  )
}

export default ForecastPopup
