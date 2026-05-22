import { fetchSpotRequests, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import SpotForecastForm from '@/features/smurfi/components/forecastForm/SpotForecastForm'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import { AppDispatch } from '@/app/store'
import { Alert, Box, Button, CircularProgress, Typography } from '@mui/material'
import { SMURFI_DASHBOARD_ROUTE } from '@wps/utils/constants'
import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate, useParams } from 'react-router-dom'

const SpotForecastFormPage = () => {
  const navigate = useNavigate()
  const dispatch: AppDispatch = useDispatch()
  const { id } = useParams()
  const spotRequestId = Number(id)
  const { spotRequests, spotRequestsLoading, spotRequestsError } = useSelector(selectSmurfi)
  const [hasRequestedSpotRequests, setHasRequestedSpotRequests] = useState(false)
  const spotRequest = spotRequests.find(request => request.id === spotRequestId)
  const { isForecaster } = useSpotPermissions(spotRequest)
  const forecastsRoute = `${SMURFI_DASHBOARD_ROUTE}/${spotRequestId}/forecasts`

  useEffect(() => {
    if (spotRequests.length === 0) {
      dispatch(fetchSpotRequests())
    }
    setHasRequestedSpotRequests(true)
  }, [dispatch, spotRequests.length])

  if (!hasRequestedSpotRequests || spotRequestsLoading) {
    return <CircularProgress aria-label="Loading spot request" />
  }

  if (spotRequestsError) {
    return <Alert severity="error">Unable to load spot request.</Alert>
  }

  if (!Number.isFinite(spotRequestId) || !spotRequest) {
    return <Alert severity="warning">Spot request not found.</Alert>
  }

  if (!isForecaster) {
    return <Alert severity="warning">You do not have permission to submit spot forecasts.</Alert>
  }

  return (
    <Box sx={{ width: '100%', maxWidth: 1440, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4">Submit Spot Forecast</Typography>
          <Typography variant="body2" color="text.secondary">
            Spot ID: {spotRequest.id}
          </Typography>
        </Box>
        <Button variant="outlined" onClick={() => navigate(forecastsRoute)}>
          Back to Forecasts
        </Button>
      </Box>
      <SpotForecastForm spotRequest={spotRequest} onSubmitSuccess={() => navigate(forecastsRoute)} />
    </Box>
  )
}

export default SpotForecastFormPage
