import React from 'react'
import { Box, Button, Typography } from '@mui/material'
import { SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { SpotRequestStatusColorMap } from '@/features/smurfi/interfaces'
import { statusToPath } from '@/features/smurfi/components/map/SpotStatusMarkers'
import SpotSubscriptionButton from '@/features/smurfi/components/SpotSubscriptionButton'

interface SpotPopupProps {
  lat: number
  lng: number
  status: SpotRequestStatus
  fireNumber: string
  spotId: number
  spotRequest: SpotRequestOutput
  canSubmitForecast: boolean
  onOpenRequest: (spotId: number) => void
  onOpenForecast: (spotId: number) => void
  onSubmitForecast: (spotId: number) => void
}

const SpotPopup: React.FC<SpotPopupProps> = ({
  lat,
  lng,
  status,
  fireNumber,
  spotId,
  spotRequest,
  canSubmitForecast,
  onOpenRequest,
  onOpenForecast,
  onSubmitForecast
}) => {
  const statusColors = SpotRequestStatusColorMap[status]
  const locationLabel = spotRequest.latest_forecast ? 'Last forecasted location' : 'Requested location'

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
          <Button
            startIcon={
              <img
                src={statusToPath[status]}
                alt="status"
                style={{
                  width: 18,
                  height: 24
                }}
              />
            }
            size="small"
            disabled
            sx={{
              backgroundColor: statusColors.bgColor,
              color: statusColors.color,
              border: `1px solid ${statusColors.borderColor}`,
              '&.Mui-disabled': { color: statusColors.color }
            }}
          >
            {status}
          </Button>
        </Box>
      </Box>
      <Box sx={{ mb: 2 }}>
        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>
          {locationLabel}
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          Lat: {lat.toFixed(6)}, Lng: {lng.toFixed(6)}
        </Typography>
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
