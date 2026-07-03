import { DateTime } from 'luxon'
import { afterEach, describe, expect, it, vi } from 'vitest'
import axios from './axios'
import {
  postSpotForecast,
  postSpotRequest,
  type SpotForecastInput,
  type SpotForecastType,
  type SpotRequestEditInput,
  type SpotRequestInput,
  SpotRequestStatus
} from './SMURFIAPI'
import type { SpotFormData } from './schema/spotForecastSchema'
import type { SpotRequestFormData } from './schema/spotRequestSchema'

describe('SMURFIAPI', () => {
  const now = new Date('2026-05-20T18:30:00.000Z')

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  const buildSpotRequestFormData = (): SpotRequestFormData => ({
    fireNumbers: ['V12345'],
    fireCentreId: 6,
    forecastStartDate: DateTime.fromISO('2026-05-21T10:00:00', { zone: 'America/Vancouver' }),
    forecastEndDate: DateTime.fromISO('2026-05-23T10:00:00', { zone: 'America/Vancouver' }),
    forecastType: 'Full',
    emailDistributionList: ['requestor@example.com', 'fban@example.com'],
    distributionGroupIds: [3, 7],
    requestedFrequency: ['Monday', 'Wednesday'],
    location: { latitude: 50.1234, longitude: -122.5678 },
    geographicDescription: 'Clearwater Valley',
    slopeAspect: 'North',
    elevation: '1000',
    additionalInformation: 'Access by helicopter only.'
  })

  const buildSpotForecastFormData = (): SpotFormData => ({
    issuedDate: DateTime.fromISO('2026-05-21T14:30:00', { zone: 'America/Vancouver' }),
    expiryDate: DateTime.fromISO('2026-05-22T14:30:00', { zone: 'America/Vancouver' }),
    forecasterPhone: ' 250-555-0100 ',
    fireProj: 'V12345',
    requestBy: 'Incident Commander',
    stns: [101, 202],
    latitude: '50.1234',
    longitude: '-122.5678',
    geographicDescription: 'Clearwater Valley',
    slopeAspect: 'North',
    valley: '',
    elevation: '1000.9',
    fireSizes: ['12.5', '-', ''],
    synopsis: 'High pressure building.',
    afternoonForecast: {
      description: 'Sunny',
      maxTemp: 22,
      minRh: 35
    },
    tonightForecast: {
      description: '',
      minTemp: 5,
      maxRh: 80
    },
    tomorrowForecast: {
      description: 'Cloudy',
      maxTemp: 18,
      minRh: 45
    },
    weatherData: [
      {
        dateTime: '2026-05-21 14:00',
        temp: '',
        rh: '45',
        wind: '',
        rain: '-',
        chanceRain: '10'
      }
    ],
    inversionVenting: 'Good venting.',
    outlook: 'Dry and stable.',
    confidenceDiscussion: 'High confidence.'
  })

  it('posts new spot requests with backend create fields and distribution groups', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(now)
    const post = vi.spyOn(axios, 'post').mockResolvedValue({ data: { spot_request: { id: 42 } } })

    await postSpotRequest(buildSpotRequestFormData())

    expect(post).toHaveBeenCalledOnce()
    const [url, payload] = post.mock.calls[0] as [string, SpotRequestInput]
    expect(url).toBe('/smurfi/spot_request')
    expect(payload).toMatchObject({
      id: null,
      request_reference: 'WPS-2026-05-20T18:30:00.000Z',
      fire_number: ['V12345'],
      fire_centre: 6,
      status: SpotRequestStatus.REQUESTED,
      request_frequency: ['Monday', 'Wednesday'],
      request_type: 'Full',
      additional_information: 'Access by helicopter only.',
      initial_instance: {
        geographic_description: 'Clearwater Valley',
        aspect: 'North',
        elevation: 1000,
        valley: null,
        latitude: 50.1234,
        longitude: -122.5678
      },
      subscribers: [
        { id: null, email: 'requestor@example.com', subscriber_status: 'active' },
        { id: null, email: 'fban@example.com', subscriber_status: 'active' }
      ],
      distribution_group_ids: [3, 7]
    })
    expect(payload.requested_at).toBe('2026-05-20T18:30:00.000Z')
    expect(payload.start_at).toBe('2026-05-21T00:00:00.000-07:00')
    expect(payload.end_at).toBe('2026-05-23T23:59:00.000-07:00')
  })

  it('patches existing spot requests without create-only fields', async () => {
    const patch = vi.spyOn(axios, 'patch').mockResolvedValue({ data: { spot_request: { id: 42 } } })

    await postSpotRequest(buildSpotRequestFormData(), 42)

    expect(patch).toHaveBeenCalledOnce()
    const [url, payload] = patch.mock.calls[0] as [string, SpotRequestEditInput]
    expect(url).toBe('/smurfi/spot_requests/42')
    expect(payload).toMatchObject({
      fire_number: ['V12345'],
      fire_centre: 6,
      request_frequency: ['Monday', 'Wednesday'],
      request_type: 'Full',
      additional_information: 'Access by helicopter only.',
      request_instance: {
        geographic_description: 'Clearwater Valley',
        aspect: 'North',
        elevation: 1000,
        valley: null,
        latitude: 50.1234,
        longitude: -122.5678
      },
      subscribers: [
        { id: null, email: 'requestor@example.com', subscriber_status: 'active' },
        { id: null, email: 'fban@example.com', subscriber_status: 'active' }
      ],
      distribution_group_ids: [3, 7]
    })
    expect(payload).not.toHaveProperty('id')
    expect(payload).not.toHaveProperty('status')
    expect(payload).not.toHaveProperty('request_reference')
    expect(payload).not.toHaveProperty('requested_at')
  })

  it('marshals spot forecast form values into backend numeric and weather payloads', async () => {
    const post = vi.spyOn(axios, 'post').mockResolvedValue({ data: { spot_forecast: { id: 99 } } })

    await postSpotForecast(buildSpotForecastFormData(), 42, 'Full' satisfies SpotForecastType)

    expect(post).toHaveBeenCalledOnce()
    const [url, payload] = post.mock.calls[0] as [string, SpotForecastInput]
    expect(url).toBe('/smurfi/spot_forecast')
    expect(payload).toMatchObject({
      spot_request_base_id: 42,
      forecast_type: 'Full',
      spot_request_instance: {
        geographic_description: 'Clearwater Valley',
        aspect: 'North',
        elevation: 1000,
        valley: null,
        latitude: 50.1234,
        longitude: -122.5678
      },
      forecaster_phone: '250-555-0100',
      fire_size: [12.5, null, null],
      representative_station_codes: [101, 202],
      synopsis: 'High pressure building.',
      inversion_and_venting: 'Good venting.',
      outlook: 'Dry and stable.',
      confidence: 'High confidence.',
      descriptive_weather: [
        { period: 'Today', temperature: 22, relative_humidity: 35, conditions: 'Sunny' },
        { period: 'Tonight', temperature: 5, relative_humidity: 80, conditions: null },
        { period: 'Tomorrow', temperature: 18, relative_humidity: 45, conditions: 'Cloudy' }
      ],
      tabular_weather: [
        {
          forecast_time: '2026-05-21T14:00:00.000-07:00',
          temperature: null,
          relative_humidity: 45,
          wind: null,
          probability_of_precipitation: 10,
          precipitation_amount: null
        }
      ]
    })
    expect(payload.issued_at).toBe('2026-05-21T14:30:00.000-07:00')
    expect(payload.expires_at).toBe('2026-05-22T14:30:00.000-07:00')
  })
})
