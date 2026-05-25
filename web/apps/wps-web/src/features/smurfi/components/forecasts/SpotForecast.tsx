import { Box, CircularProgress, Typography } from '@mui/material'
import { useParams } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { fetchSpotForecasts, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import { fetchWxStations } from '@/features/stations/slices/stationsSlice'
import { selectFireWeatherStations } from '@/app/rootReducer'
import { getStations, StationSource } from '@wps/api/stationAPI'
import { spotRequestTypeMap } from '@wps/api/SMURFIAPI'
import MiniSpotForecast from '@/features/smurfi/components/forecasts/MiniSpotForecast'
import { useEffect } from 'react'
import { AppDispatch } from '@/app/store'
import FullSpotForecast from '@/features/smurfi/components/forecasts/FullSpotForecast'

const SpotForecast = () => {
  const { id, forecastId } = useParams<{ id: string; forecastId: string }>()
  const dispatch = useDispatch<AppDispatch>()
  const { spotRequests, spotRequestsLoading, spotForecastsByRequestId, spotForecastsLoading } =
    useSelector(selectSmurfi)
  const { stationsByCode, loading: stationsLoading } = useSelector(selectFireWeatherStations)

  const spotRequestId = Number(id)
  const spotForecastId = Number(forecastId)

  useEffect(() => {
    if (!spotForecastsByRequestId[spotRequestId]) {
      dispatch(fetchSpotForecasts(spotRequestId))
    }
  }, [dispatch, spotRequestId, spotForecastsByRequestId])

  useEffect(() => {
    if (Object.keys(stationsByCode).length === 0) {
      dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
    }
  }, [dispatch, stationsByCode])

  if (spotRequestsLoading || spotForecastsLoading || stationsLoading) {
    return <CircularProgress />
  }

  const spotRequest = spotRequests.find(sr => sr.id === spotRequestId)
  const spotForecast = (spotForecastsByRequestId[spotRequestId] ?? []).find(f => f.id === spotForecastId)

  if (!spotRequest || !spotForecast) {
    return <Typography>Forecast not found</Typography>
  }

  const representativeStations = (spotForecast.representative_station_codes ?? []).flatMap(code => {
    const station = stationsByCode[code]
    return station ? [{ code, name: station.properties.name, elevation: station.properties.elevation }] : []
  })

  if (spotRequest.request_type === spotRequestTypeMap['MINI_SPOT']) {
    return <MiniSpotForecast forecast={spotForecast} />
  }

  return (
    <Box sx={{ pb: 4 }}>
      <FullSpotForecast
        forecast={spotForecast}
        spotRequest={spotRequest}
        representativeStations={representativeStations}
      />
    </Box>
  )
}

export default SpotForecast
