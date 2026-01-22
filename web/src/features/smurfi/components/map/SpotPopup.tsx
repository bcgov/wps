import React from 'react'
import { Box, Button, Typography } from '@mui/material'
import NotificationsIcon from '@mui/icons-material/Notifications'
import activeSpot from './styles/activeSpot.svg'
import completeSpot from './styles/completeSpot.svg'
import pendingSpot from './styles/newSpotRequest.svg'
import pausedSpot from './styles/onHoldSpot.svg'

type SpotRequestStatus = 'ACTIVE' | 'COMPLETE' | 'PENDING' | 'PAUSED'

export const statusToPath: Record<SpotRequestStatus, string> = {
  ACTIVE: activeSpot,
  COMPLETE: completeSpot,
  PENDING: pendingSpot,
  PAUSED: pausedSpot
}

interface SpotPopupProps {
  lat: number
  lng: number
  status: SpotRequestStatus
}

const SpotPopup: React.FC<SpotPopupProps> = ({ lat, lng, status }) => {
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
        <Typography variant="body2">V00000</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button startIcon={<NotificationsIcon />} size="small" variant="contained" color="primary">
            Subscribe
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
            sx={{ backgroundColor: '#e8f5e8', color: '#2e7d32', '&.Mui-disabled': { color: '#2e7d32' } }}
          >
            Active
          </Button>
        </Box>
      </Box>
      <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
        Lat: {lat.toFixed(6)}, Lng: {lng.toFixed(6)}
      </Typography>
      <Button variant="contained" color="primary" size="small" fullWidth>
        Spot Forecast
      </Button>
    </Box>
  )
}

export default SpotPopup
