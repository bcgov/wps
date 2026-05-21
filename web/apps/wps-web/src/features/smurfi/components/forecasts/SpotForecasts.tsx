import { Box } from '@mui/material'
import { useParams } from 'react-router-dom'

// Placeholder page for the SpotForecasts associated with the SpotRequested as referenced by param.id which is taken from the URL
const SpotForecasts = () => {
  const params = useParams()
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
      Placeholder for spot forecasts associated with the Spot Request specified in the URL path SpotForecast:{' '}
      {params.id}
    </Box>
  )
}

export default SpotForecasts
