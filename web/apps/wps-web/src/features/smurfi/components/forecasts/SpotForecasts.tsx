import { AppDispatch } from '@/app/store'
import { fetchSpotForecasts, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import { Box, CircularProgress, Typography } from '@mui/material'
import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useParams } from 'react-router-dom'

const SpotForecasts = () => {
  const { id } = useParams<{ id: string }>()
  const dispatch = useDispatch<AppDispatch>()
  const { spotForecastsByRequestId, spotForecastsLoading } = useSelector(selectSmurfi)

  const spotRequestId = Number(id)

  useEffect(() => {
    if (!spotForecastsByRequestId[spotRequestId]) {
      dispatch(fetchSpotForecasts(spotRequestId))
    }
  }, [dispatch, spotRequestId, spotForecastsByRequestId])

  if (spotForecastsLoading) {
    return <CircularProgress />
  }

  const forecasts = spotForecastsByRequestId[spotRequestId] ?? []

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
      <Typography>
        Spot forecasts for request {id} — {forecasts.length} forecast(s)
      </Typography>
    </Box>
  )
}

export default SpotForecasts
