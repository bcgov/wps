import React from 'react'
import { Box } from '@mui/material'
import { SpotForecastOutput } from '@wps/api/SMURFIAPI'

interface MiniSpotForecastProps {
  forecast: SpotForecastOutput
}

const MiniSpotForecast: React.FC<MiniSpotForecastProps> = ({ forecast: _ }) => {
  return <Box>Mini Spot Forecast placeholder</Box>
}

export default MiniSpotForecast
