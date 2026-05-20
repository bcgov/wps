import React from 'react'
import { Box, Button, Typography } from '@mui/material'
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive'
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone'
import { useDispatch, useSelector } from 'react-redux'
import { selectSubscribedIds, selectSubscriptionsLoading, toggleSpotSubscription } from '@/features/smurfi/slices/subscriptionsSlice'
import { AppDispatch } from '@/app/store'
import activeSpot from './styles/activeSpot.svg'
import completeSpot from './styles/completeSpot.svg'
import pendingSpot from './styles/newSpotRequest.svg'
import pausedSpot from './styles/onHoldSpot.svg'

type SpotRequestStatus = 'ACTIVE' | 'COMPLETE' | 'PENDING' | 'PAUSED' | 'INACTIVE' | 'ARCHIVED'

export const statusToPath: Record<SpotRequestStatus, string> = {
  ACTIVE: activeSpot,
  COMPLETE: completeSpot,
  PENDING: pendingSpot,
  PAUSED: pausedSpot,
  INACTIVE: completeSpot,
  ARCHIVED: completeSpot
}

const getStatusBackgroundColor = (status: SpotRequestStatus): { backgroundColor: string; color: string } => {
  switch (status) {
    case 'ACTIVE':
      return { backgroundColor: '#e8f5e9', color: '#2e7d32' } // green
    case 'PAUSED':
      return { backgroundColor: '#fff8e1', color: '#f57f17' } // yellow
    case 'INACTIVE':
    case 'ARCHIVED':
      return { backgroundColor: '#ffebee', color: '#000000' } // black
    case 'COMPLETE':
      return { backgroundColor: '#ffebee', color: '#c62828' } // red
    case 'PENDING':
    default:
      return { backgroundColor: '#e3f2fd', color: '#1565c0' } // blue (default)
  }
}

interface SpotPopupProps {
  lat: number
  lng: number
  status: SpotRequestStatus
  fireNumber: string
  spotId: number
  onOpenForecast: (fireNumber: string, lat?: number, lng?: number) => void
}

const SpotPopup: React.FC<SpotPopupProps> = ({ lat, lng, status, fireNumber, spotId, onOpenForecast }) => {
  const dispatch = useDispatch<AppDispatch>()
  const subscribedIds = useSelector(selectSubscribedIds)
  const isLoading = useSelector(selectSubscriptionsLoading)
  const isSubscribed = subscribedIds.includes(spotId)
  const statusColors = getStatusBackgroundColor(status)

  const handleSpotForecastClick = (event: React.MouseEvent) => {
    event.stopPropagation()
    event.preventDefault()
    onOpenForecast(fireNumber, lat, lng)
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
              backgroundColor: statusColors.backgroundColor,
              color: statusColors.color,
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
        Spot Forecast
      </Button>
    </Box>
  )
}

export default SpotPopup
