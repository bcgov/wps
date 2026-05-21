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
import activeSpot from './styles/activeSpot.svg'
import completeSpot from './styles/completeSpot.svg'
import pendingSpot from './styles/newSpotRequest.svg'
import pausedSpot from './styles/onHoldSpot.svg'
import { SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { SpotRequestStatusColorMap } from '@/features/smurfi/interfaces'

export const statusToPath: Record<SpotRequestStatus, string> = {
  [SpotRequestStatus.REQUESTED]: pendingSpot,
  [SpotRequestStatus.STARTED]: activeSpot,
  [SpotRequestStatus.SUSPENDED]: pausedSpot,
  [SpotRequestStatus.COMPLETE]: completeSpot,
  [SpotRequestStatus.ARCHIVED]: completeSpot
}

interface SpotPopupProps {
  lat: number
  lng: number
  status: SpotRequestStatus
  fireNumber: string
  spotId: number
  onOpenForecast: (spotId: number) => void
}

const SpotPopup: React.FC<SpotPopupProps> = ({ lat, lng, status, fireNumber, spotId, onOpenForecast }) => {
  const dispatch = useDispatch<AppDispatch>()
  const subscribedIds = useSelector(selectSubscribedIds)
  const isLoading = useSelector(selectSubscriptionsLoading)
  const isSubscribed = subscribedIds.includes(spotId)
  const statusColors = SpotRequestStatusColorMap[status]

  const handleSpotForecastClick = (event: React.MouseEvent) => {
    event.stopPropagation()
    event.preventDefault()
    onOpenForecast(spotId)
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
                  width: 20,
                  height: 20
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
      <Button variant="contained" color="primary" size="small" fullWidth onClick={handleSpotForecastClick}>
        View Forecasts
      </Button>
    </Box>
  )
}

export default SpotPopup
