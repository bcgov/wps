import React from 'react'
import { Box, Button, Typography } from '@mui/material'
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive'
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone'
import { useDispatch, useSelector } from 'react-redux'
import {
  selectSubscribedIds,
  selectSubscriptionsLoading,
  toggleSpotSubscription
} from '@/features/smurfi/slices/subscriptionsSlice'
import { AppDispatch } from '@/app/store'
import { SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { SpotRequestStatusColorMap } from '@/features/smurfi/interfaces'
import { statusToPath } from '@/features/smurfi/components/map/SpotStatusMarkers'

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
  onSubmitForecast: (spotRequest: SpotRequestOutput) => void
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
  const dispatch = useDispatch<AppDispatch>()
  const subscribedIds = useSelector(selectSubscribedIds)
  const isLoading = useSelector(selectSubscriptionsLoading)
  const isSubscribed = subscribedIds.includes(spotId)
  const statusColors = SpotRequestStatusColorMap[status]

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
    onSubmitForecast(spotRequest)
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
          <Button
            startIcon={isSubscribed ? <NotificationsActiveIcon /> : <NotificationsNoneIcon />}
            size="small"
            variant="contained"
            color="primary"
            disabled={isLoading}
            onClick={() => dispatch(toggleSpotSubscription(spotId))}
          >
            {isSubscribed ? 'Unsubscribe' : 'Subscribe'}
          </Button>
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
      <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
        Lat: {lat.toFixed(6)}, Lng: {lng.toFixed(6)}
      </Typography>
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
