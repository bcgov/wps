import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { fetchSpotForecasts, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import { AppDispatch } from '@/app/store'
import { Alert, Box, Button, CircularProgress, Typography } from '@mui/material'
import { DateTime } from 'luxon'
import SpotForecastForm from '@/features/smurfi/components/forecastForm/SpotForecastForm'
import { getSmurfiForecastsRoute } from '@wps/utils/constants'

const EditSpotForecastPage = () => {
  const { id, forecastId } = useParams<{ id: string; forecastId: string }>()
  const navigate = useNavigate()
  const dispatch = useDispatch<AppDispatch>()
  const { spotRequests, spotRequestsLoading, spotRequestsError, spotForecastsByRequestId, spotForecastsLoading } =
    useSelector(selectSmurfi)

  const spotRequestId = Number(id)
  const spotForecastId = Number(forecastId)
  const forecastsRoute = getSmurfiForecastsRoute(spotRequestId)

  useEffect(() => {
    if (Number.isFinite(spotRequestId) && !spotForecastsByRequestId[spotRequestId]) {
      dispatch(fetchSpotForecasts(spotRequestId))
    }
  }, [dispatch, spotRequestId, spotForecastsByRequestId])

  const spotRequest = spotRequests.find(sr => sr.id === spotRequestId)
  const { isForecaster } = useSpotPermissions(spotRequest)
  const spotForecast = (spotForecastsByRequestId[spotRequestId] ?? []).find(f => f.id === spotForecastId)

  if (spotRequestsLoading || spotForecastsLoading) {
    return <CircularProgress aria-label="Loading spot forecast" />
  }

  if (spotRequestsError) {
    return <Alert severity="error">Unable to load spot request.</Alert>
  }

  if (!Number.isFinite(spotRequestId) || !Number.isFinite(spotForecastId) || !spotRequest) {
    return <Alert severity="warning">Spot forecast not found.</Alert>
  }

  if (!isForecaster) {
    return <Alert severity="warning">You do not have permission to edit this forecast.</Alert>
  }

  if (!spotForecast) {
    return <Alert severity="warning">Spot forecast not found.</Alert>
  }

  if (spotForecast?.expires_at) {
    const expiry = DateTime.fromISO(spotForecast.expires_at)
    if (expiry.isValid && expiry < DateTime.now()) {
      return <Alert severity="warning">This forecast is expired and can&apos;t be edited.</Alert>
    }
  }

  return (
    <Box sx={{ width: '100%', maxWidth: 1440, mx: 'auto', pb: 6 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4">Edit Spot Forecast</Typography>
          <Typography variant="body2" color="text.secondary">
            Previous Forecast ID: {spotForecast.id}
          </Typography>
        </Box>
        <Button variant="outlined" onClick={() => navigate(forecastsRoute)}>
          View Forecasts
        </Button>
      </Box>
      <SpotForecastForm
        spotRequest={spotRequest}
        sourceForecast={spotForecast}
        prefillFullForecast={true}
        onSubmitSuccess={() => navigate(forecastsRoute)}
      />
    </Box>
  )
}

export default EditSpotForecastPage
