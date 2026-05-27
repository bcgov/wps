import { AppDispatch } from '@/app/store'
import { fetchSpotForecasts, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import SpotForecastForm from '@/features/smurfi/components/forecastForm/SpotForecastForm'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import { getMostRecentForecast } from '@/features/smurfi/utils/spotForecastUtils'
import { Alert, Box, Button, CircularProgress, Typography } from '@mui/material'
import { getSmurfiForecastsRoute } from '@wps/utils/constants'
import { useEffect, useMemo } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate, useParams } from 'react-router-dom'

const SpotForecastFormPage = () => {
  const dispatch = useDispatch<AppDispatch>()
  const navigate = useNavigate()
  const { id } = useParams()
  const spotRequestId = Number(id)
  const { spotRequests, spotRequestsLoading, spotRequestsError, spotForecastsByRequestId, spotForecastsError } =
    useSelector(selectSmurfi)
  const spotRequest = spotRequests.find(request => request.id === spotRequestId)
  const { isForecaster } = useSpotPermissions(spotRequest)
  const forecastsRoute = getSmurfiForecastsRoute(spotRequestId)
  const spotForecasts = spotForecastsByRequestId[spotRequestId]
  const carryForwardForecast = useMemo(() => getMostRecentForecast(spotForecasts ?? []), [spotForecasts])

  useEffect(() => {
    if (Number.isFinite(spotRequestId) && spotForecastsByRequestId[spotRequestId] === undefined) {
      dispatch(fetchSpotForecasts(spotRequestId))
    }
  }, [dispatch, spotForecastsByRequestId, spotRequestId])

  if (spotRequestsLoading) {
    return <CircularProgress aria-label="Loading spot request" />
  }

  if (spotRequestsError) {
    return <Alert severity="error">Unable to load spot request.</Alert>
  }

  if (!Number.isFinite(spotRequestId) || !spotRequest) {
    return <Alert severity="warning">Spot request not found.</Alert>
  }

  if (spotForecasts === undefined && !spotForecastsError) {
    return <CircularProgress aria-label="Loading previous spot forecasts" />
  }

  if (!isForecaster) {
    return <Alert severity="warning">You do not have permission to submit spot forecasts.</Alert>
  }

  return (
    <Box sx={{ width: '100%', maxWidth: 1440, mx: 'auto', pb: 6 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4">Submit Spot Forecast</Typography>
          <Typography variant="body2" color="text.secondary">
            Spot ID: {spotRequest.id}
          </Typography>
        </Box>
        <Button variant="outlined" onClick={() => navigate(forecastsRoute)}>
          View Forecasts
        </Button>
      </Box>
      <SpotForecastForm
        spotRequest={spotRequest}
        sourceForecast={carryForwardForecast}
        onSubmitSuccess={() => navigate(forecastsRoute)}
      />
    </Box>
  )
}

export default SpotForecastFormPage
