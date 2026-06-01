import { Box, CircularProgress, Typography } from '@mui/material'
import PrintableFullSpotForecast from '@/features/smurfi/components/forecasts/PrintableFullSpotForecast'
import PrintableMiniSpotForecast from '@/features/smurfi/components/forecasts/PrintableMiniSpotForecast'
import useSpotForecastData from '@/features/smurfi/hooks/useSpotForecastData'

const PrintableSpotForecast = () => {
  const { loading, spotRequest, spotForecast, representativeStations } = useSpotForecastData()

  if (loading) {
    return <CircularProgress />
  }

  if (!spotRequest || !spotForecast) {
    return <Typography>Forecast not found</Typography>
  }

  const props = { forecast: spotForecast, spotRequest, representativeStations }

  return (
    <Box sx={{ p: 3 }}>
      {spotForecast.forecast_type === 'Mini' ? (
        <PrintableMiniSpotForecast {...props} />
      ) : (
        <PrintableFullSpotForecast {...props} />
      )}
    </Box>
  )
}

export default PrintableSpotForecast
