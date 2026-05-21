import { Box } from '@mui/material'
import { useParams } from 'react-router-dom'

// Placeholder page for a single SpotForecast associated with a SpotRequest as referenced by param.id which is taken from the URL
const SpotForecast = () => {
  const params = useParams()
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
      Placeholder for a single spot forecast associated with the Spot Request specified in the URL path SpotRequest:{' '}
      {params.id} and {params.forecastId}
    </Box>
  )
}

export default SpotForecast
