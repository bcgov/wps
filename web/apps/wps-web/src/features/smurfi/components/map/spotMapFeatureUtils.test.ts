import { SpotForecastOutput, SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { buildSpotFeature, getForecastFeaturesForRequest } from './spotMapFeatureUtils'

const spotRequest = {
  id: 42,
  fire_number: ['V12345'],
  status: SpotRequestStatus.STARTED,
  request_instance: {
    id: 1,
    geographic_description: 'Requested ridge',
    latitude: 48.5,
    longitude: -123.5,
    created_at: '2026-05-21T00:00:00Z'
  }
} as SpotRequestOutput

const buildForecast = (
  id: number,
  latitude: number,
  longitude: number,
  issuedAt = '2026-05-22T18:00:00Z',
  createdAt = issuedAt
) =>
  ({
    id,
    spot_request_base_id: spotRequest.id,
    forecast_type: 'Full',
    issued_at: issuedAt,
    created_at: createdAt,
    forecaster_name: 'Test Forecaster',
    forecaster_email: 'forecaster@example.com',
    spot_request_instance_id: id,
    spot_request_instance: {
      id,
      geographic_description: 'Forecast location',
      latitude,
      longitude,
      created_at: '2026-05-22T18:00:00Z'
    },
    descriptive_weather: [],
    tabular_weather: []
  }) as SpotForecastOutput

describe('spotMapFeatureUtils', () => {
  it('builds request marker features from the requested location', () => {
    const feature = buildSpotFeature(spotRequest)

    expect(feature.lat).toBe(spotRequest.request_instance.latitude)
    expect(feature.lon).toBe(spotRequest.request_instance.longitude)
  })

  it('omits forecast markers that share the requested location', () => {
    const forecastFeatures = getForecastFeaturesForRequest(spotRequest, [buildForecast(10, 48.5, -123.5)])

    expect(forecastFeatures).toHaveLength(0)
  })

  it('builds forecast markers for forecast locations away from the requested location', () => {
    const forecastFeatures = getForecastFeaturesForRequest(spotRequest, [
      buildForecast(10, 48.5, -123.5),
      buildForecast(11, 48.501, -123.5)
    ])

    expect(forecastFeatures).toHaveLength(1)
    expect(forecastFeatures[0].latestForecast.id).toBe(11)
  })

  it('groups forecasts that share a forecast location', () => {
    const forecastFeatures = getForecastFeaturesForRequest(spotRequest, [
      buildForecast(11, 48.501, -123.5, '2026-05-23T18:00:00Z', '2026-05-22T18:00:00Z'),
      buildForecast(12, 48.50105, -123.50005, '2026-05-22T18:00:00Z', '2026-05-23T18:00:00Z')
    ])

    expect(forecastFeatures).toHaveLength(1)
    expect(forecastFeatures[0].forecastCount).toBe(2)
    expect(forecastFeatures[0].forecasts.map(forecast => forecast.id)).toEqual([11, 12])
    expect(forecastFeatures[0].latestForecast.id).toBe(12)
  })
})
