import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { fetchSpotForecasts, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import { AppDispatch } from '@/app/store'
import { Typography } from '@mui/material'
import { DateTime } from 'luxon'

const EditSpotForecastPage = () => {
  const { id, forecastId } = useParams<{ id: string; forecastId: string }>()
  const dispatch = useDispatch<AppDispatch>()
  const { spotRequests, spotForecastsByRequestId } = useSelector(selectSmurfi)

  const spotRequestId = Number(id)
  const spotForecastId = Number(forecastId)

  useEffect(() => {
    if (!spotForecastsByRequestId[spotRequestId]) {
      dispatch(fetchSpotForecasts(spotRequestId))
    }
  }, [dispatch, spotRequestId, spotForecastsByRequestId])

  const spotRequest = spotRequests.find(sr => sr.id === spotRequestId)
  const { isForecaster } = useSpotPermissions(spotRequest)

  if (!isForecaster) {
    return <Typography>You do not have permission to edit this forecast.</Typography>
  }

  const spotForecast = (spotForecastsByRequestId[spotRequestId] ?? []).find(f => f.id === spotForecastId)
  if (spotForecast?.expires_at) {
    const expiry = DateTime.fromISO(spotForecast.expires_at)
    if (expiry.isValid && expiry < DateTime.now()) {
      return <Typography>This forecast is expired and can&apos;t be edited.</Typography>
    }
  }

  return <Typography>Edit Spot Forecast</Typography>
}

export default EditSpotForecastPage
