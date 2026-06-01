import React from 'react'
import { useParams } from 'react-router-dom'
import { Box, Typography } from '@mui/material'
import { GeneralHeader } from '@wps/ui/GeneralHeader'

const SpotDetailPage: React.FC = () => {
  const { spotId } = useParams<{ spotId: string }>()

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <GeneralHeader isBeta={true} spacing={1} title="Spot Forecast" />
      <Box sx={{ p: 3 }}>
        <Typography variant="h5">Spot Forecast #{spotId}</Typography>
        <Typography variant="body1" sx={{ mt: 2 }}>
          Spot forecast details for request {spotId}.
        </Typography>
      </Box>
    </Box>
  )
}

export default SpotDetailPage
