import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { fetchSpotForecasts, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import { fetchWxStations } from '@/features/stations/slices/stationsSlice'
import { selectFireWeatherStations } from '@/app/rootReducer'
import { getStations, StationSource } from '@wps/api/stationAPI'
import { AppDispatch } from '@/app/store'
import { RepresentativeStation } from '@/features/smurfi/interfaces'
import { SpotForecastOutput, SpotRequestOutput } from '@wps/api/SMURFIAPI'

interface SpotForecastData {
  loading: boolean
  spotRequest: SpotRequestOutput | undefined
  spotForecast: SpotForecastOutput | undefined
  representativeStations: RepresentativeStation[]
}

const useSpotForecastData = (): SpotForecastData => {
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

  const loading = spotRequestsLoading || spotForecastsLoading || stationsLoading
  const spotRequest = spotRequests.find(sr => sr.id === spotRequestId)
  const spotForecast = (spotForecastsByRequestId[spotRequestId] ?? []).find(f => f.id === spotForecastId)

  const representativeStations: RepresentativeStation[] = (spotForecast?.representative_station_codes ?? []).flatMap(
    code => {
      const station = stationsByCode[code]
      return station ? [{ code, name: station.properties.name, elevation: station.properties.elevation }] : []
    }
  )

  return { loading, spotRequest, spotForecast, representativeStations }
}

export default useSpotForecastData
