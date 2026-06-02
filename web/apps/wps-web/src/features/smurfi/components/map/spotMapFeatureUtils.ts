import { ForecastFeature, SpotFeature } from '@/features/smurfi/interfaces'
import { formatFireNumbers } from '@/features/smurfi/utils/spotForecastUtils'
import { SpotForecastOutput, SpotRequestOutput } from '@wps/api/SMURFIAPI'

export const COORDINATE_TOLERANCE = 0.0001

export const locationsMatch = (
  first: { latitude: number; longitude: number },
  second: { latitude: number; longitude: number }
) =>
  Math.abs(first.latitude - second.latitude) < COORDINATE_TOLERANCE &&
  Math.abs(first.longitude - second.longitude) < COORDINATE_TOLERANCE

export const buildSpotFeature = (spotRequest: SpotRequestOutput): SpotFeature => {
  const instance = spotRequest.request_instance
  return {
    lon: instance.longitude,
    lat: instance.latitude,
    status: spotRequest.status,
    id: String(spotRequest.id),
    spotId: spotRequest.id,
    fireNumber: formatFireNumbers(spotRequest.fire_number),
    spotRequest,
    locationType: 'requested'
  }
}

export const buildForecastFeature = (spotRequest: SpotRequestOutput, forecast: SpotForecastOutput): ForecastFeature => {
  const instance = forecast.spot_request_instance
  return {
    lon: instance.longitude,
    lat: instance.latitude,
    status: spotRequest.status,
    id: String(forecast.id),
    spotId: spotRequest.id,
    fireNumber: formatFireNumbers(spotRequest.fire_number),
    spotRequest,
    forecastCount: 1,
    forecasts: [forecast],
    latestForecast: forecast
  }
}

const getLatestForecast = (forecasts: SpotForecastOutput[]): SpotForecastOutput =>
  forecasts.reduce((latest, forecast) =>
    Date.parse(forecast.created_at) > Date.parse(latest.created_at) ? forecast : latest
  )

const groupForecastsByLocation = (forecasts: SpotForecastOutput[]): SpotForecastOutput[][] =>
  forecasts.reduce<SpotForecastOutput[][]>((groups, forecast) => {
    const existingGroup = groups.find(group =>
      locationsMatch(
        {
          latitude: group[0].spot_request_instance.latitude,
          longitude: group[0].spot_request_instance.longitude
        },
        {
          latitude: forecast.spot_request_instance.latitude,
          longitude: forecast.spot_request_instance.longitude
        }
      )
    )

    if (existingGroup) {
      existingGroup.push(forecast)
      return groups
    }

    groups.push([forecast])
    return groups
  }, [])

export const getForecastFeaturesForRequest = (
  spotRequest: SpotRequestOutput,
  forecasts: SpotForecastOutput[]
): ForecastFeature[] => {
  const requestLocation = spotRequest.request_instance
  return groupForecastsByLocation(
    forecasts.filter(
      forecast =>
        !locationsMatch(requestLocation, {
          latitude: forecast.spot_request_instance.latitude,
          longitude: forecast.spot_request_instance.longitude
        })
    )
  ).map(group => {
    const latestForecast = getLatestForecast(group)
    return {
      ...buildForecastFeature(spotRequest, latestForecast),
      id: group.map(forecast => forecast.id).join('-'),
      forecastCount: group.length,
      forecasts: group,
      latestForecast
    }
  })
}
