import { Box, Button, CircularProgress, Paper, Typography } from '@mui/material'
import { useNavigate, useParams } from 'react-router-dom'
import MiniSpotForecast from '@/features/smurfi/components/forecasts/MiniSpotForecast'
import FullSpotForecast from '@/features/smurfi/components/forecasts/FullSpotForecast'
import { getSmurfiForecastPrintRoute } from '@wps/utils/constants'
import useSpotForecastData from '@/features/smurfi/hooks/useSpotForecastData'
import SpotRequestLocationMap from '@/features/smurfi/components/requestForm/SpotRequestLocationMap'
import { SpotRequestOutput } from '@wps/api/SMURFIAPI'

const SpotForecast = () => {
  const { id, forecastId } = useParams<{ id: string; forecastId: string }>()
  const navigate = useNavigate()
  const { loading, spotRequest, spotForecast, representativeStations } = useSpotForecastData()

  const spotRequestId = Number(id)
  const spotForecastId = Number(forecastId)

  if (loading) {
    return <CircularProgress />
  }

  if (!spotRequest || !spotForecast) {
    return <Typography>Forecast not found</Typography>
  }

  const printUrl = getSmurfiForecastPrintRoute(spotRequestId, spotForecastId)
  const isMini = spotForecast.forecast_type === 'Mini'
  const forecastLocation = {
    latitude: spotForecast.spot_request_instance.latitude,
    longitude: spotForecast.spot_request_instance.longitude
  }
  const forecastLocationSpotRequest: SpotRequestOutput = {
    ...spotRequest,
    current_instance: spotForecast.spot_request_instance
  }

  return (
    <Box sx={{ pb: 4 }}>
      <Box sx={{ mb: 1 }}>
        <Button variant="outlined" onClick={() => navigate(printUrl)} size="small">
          Printable Version
        </Button>
      </Box>
      {isMini ? (
        <MiniSpotForecast
          forecast={spotForecast}
          spotRequest={spotRequest}
          representativeStations={representativeStations}
        />
      ) : (
        <FullSpotForecast
          forecast={spotForecast}
          spotRequest={spotRequest}
          representativeStations={representativeStations}
        />
      )}
      <Paper variant="outlined" sx={{ p: 2.5, mt: 2 }}>
        <SpotRequestLocationMap
          selectedLocation={forecastLocation}
          existingSpotRequests={[forecastLocationSpotRequest]}
          focusOnSelectedLocation
          readOnly
          showSelectedLocationMarker={false}
        />
      </Paper>
    </Box>
  )
}

export default SpotForecast
