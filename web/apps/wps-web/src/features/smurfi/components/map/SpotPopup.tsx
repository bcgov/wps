import React from 'react'
import { Box, Button, Typography } from '@mui/material'
import { SpotPopupData } from '@/features/smurfi/interfaces'
import SpotSubscriptionButton from '@/features/smurfi/components/SpotSubscriptionButton'
import SpotStatusControl from '@/features/smurfi/components/SpotStatusControl'
import { SpotRequestOutput } from '@wps/api/SMURFIAPI'

interface SpotPopupProps {
  popupData: SpotPopupData
  canSubmitForecast: boolean
  onOpenRequest: (spotId: number) => void
  onOpenForecast: (spotId: number) => void
  onSubmitForecast: (spotId: number) => void
  onStatusChanged?: (spotRequest: SpotRequestOutput) => void
}

const SpotPopup: React.FC<SpotPopupProps> = ({
  popupData,
  canSubmitForecast,
  onOpenRequest,
  onOpenForecast,
  onSubmitForecast,
  onStatusChanged
}) => {
  const { lat, lng, fireNumber, spotId, spotRequest } = popupData

  const handleRequestClick = (event: React.MouseEvent) => {
    event.stopPropagation()
    event.preventDefault()
    onOpenRequest(spotId)
  }

  const handleSpotForecastClick = (event: React.MouseEvent) => {
    event.stopPropagation()
    event.preventDefault()
    onOpenForecast(spotId)
  }

  const handleSubmitForecastClick = (event: React.MouseEvent) => {
    event.stopPropagation()
    event.preventDefault()
    onSubmitForecast(spotId)
  }

  return (
    <Box
      sx={{
        p: 2,
        background: 'white',
        border: '1px solid #ddd',
        borderRadius: 2,
        boxShadow: 3,
        minWidth: 320,
        maxWidth: 350
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="body2">{fireNumber}</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <SpotSubscriptionButton spotRequest={spotRequest} variant="contained" />
          <Box sx={{ flex: '0 0 132px', width: 132 }}>
            <SpotStatusControl spotRequest={spotRequest} fullWidth onStatusChanged={onStatusChanged} />
          </Box>
        </Box>
      </Box>
      <Box sx={{ mb: 2 }}>
        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>
          Requested location
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          Lat: {lat.toFixed(6)}, Lng: {lng.toFixed(6)}
        </Typography>
        {spotRequest.latest_forecast?.forecaster_name && (
          <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>
            <Box component="span" sx={{ fontWeight: 600 }}>
              Last Forecast By:
            </Box>{' '}
            {spotRequest.latest_forecast.forecaster_name}
          </Typography>
        )}
      </Box>
      <Box sx={{ display: 'flex', gap: 1 }}>
        <Button variant="outlined" color="primary" size="small" fullWidth onClick={handleRequestClick}>
          View Request
        </Button>
        <Button variant="contained" color="primary" size="small" fullWidth onClick={handleSpotForecastClick}>
          View Forecasts
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

export default SpotPopup
