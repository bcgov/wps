import axios from './axios'
import { SpotFormData } from './schema/spotForecastSchema'
import { SpotRequestFormData } from './schema/spotRequestSchema'

export enum SpotRequestStatus {
  REQUESTED = 'Requested',
  STARTED = 'Started',
  SUSPENDED = 'Suspended',
  COMPLETE = 'Complete',
  ARCHIVED = 'Archived'
}

export interface SpotAdminRow {
  id: number
  spot_id: number
  fire_id: string
  forecaster: string
  fire_centre: string
  status: SpotRequestStatus
  last_updated: number | null
  latitude: number
  longitude: number
  spot_start: number
  spot_end: number
}

export interface SpotAdminRowResponse {
  rows: SpotAdminRow[]
}

export interface SpotForecastInput {
  issued_date: string
  expiry_date: string
  fire_project: string
  request_by: string
  forecast_by: string
  email: string
  phone: string
  city: string
  stations?: number[]
  latitude: number
  longitude: number
  slope_aspect: string
  valley?: string
  elevation?: string
  size?: string
  synopsis: string
  afternoon_forecast?: {
    description: string
    max_temp: number
    min_rh: number
  }
  tonight_forecast?: {
    description: string
    min_temp: number
    max_rh: number
  }
  tomorrow_forecast?: {
    description: string
    max_temp: number
    min_rh: number
  }
  weather_data: {
    date_time: string
    temp: number | null
    rh: number | null
    wind_speed: number | null
    wind_gust: number | null
    wind_direction: number | null
    rain: number | null
    chance_rain: number | null
  }[]
  inversion_venting: string
  outlook?: string
  confidence_discussion: string
}

const marshalFormDataToSpotForecastInput = (formData: SpotFormData): SpotForecastInput => {
  return {
    issued_date: formData.issuedDate.toISO()!,
    expiry_date: formData.expiryDate.toISO()!,
    fire_project: formData.fireProj,
    request_by: formData.requestBy,
    forecast_by: formData.forecastBy,
    email: formData.email,
    phone: formData.phone,
    city: formData.city,
    stations: formData.stns,
    latitude: Number(formData.latitude),
    longitude: Number(formData.longitude),
    slope_aspect: formData.slopeAspect,
    valley: formData.valley,
    elevation: formData.elevation,
    size: formData.size,
    synopsis: formData.synopsis,
    afternoon_forecast: formData.afternoonForecast
      ? {
          description: formData.afternoonForecast.description || '',
          max_temp: formData.afternoonForecast.maxTemp || 0,
          min_rh: formData.afternoonForecast.minRh || 0
        }
      : undefined,
    tonight_forecast: formData.tonightForecast
      ? {
          description: formData.tonightForecast.description || '',
          min_temp: formData.tonightForecast.minTemp || 0,
          max_rh: formData.tonightForecast.maxRh || 0
        }
      : undefined,
    tomorrow_forecast: formData.tomorrowForecast
      ? {
          description: formData.tomorrowForecast.description || '',
          max_temp: formData.tomorrowForecast.maxTemp || 0,
          min_rh: formData.tomorrowForecast.minRh || 0
        }
      : undefined,
    weather_data: formData.weatherData.map(row => ({
      date_time: row.dateTime,
      temp: row.temp ? Number(row.temp) : null,
      rh: row.rh ? Number(row.rh) : null,
      wind_speed: row.windSpeed ? Number(row.windSpeed) : null,
      wind_gust: row.windGust ? Number(row.windGust) : null,
      wind_direction: row.windDirection ? Number(row.windDirection) : null,
      rain: row.rain ? Number(row.rain) : null,
      chance_rain: row.chanceRain ? Number(row.chanceRain) : null
    })),
    inversion_venting: formData.inversionVenting,
    outlook: formData.outlook,
    confidence_discussion: formData.confidenceDiscussion
  }
}
export interface SpotForecastOutput extends SpotForecastInput {
  id: number
  create_timestamp: string
  create_user: string
  update_timestamp: string
  update_user: string
}

export interface SpotForecastResponse {
  spot_forecast: SpotForecastOutput
}

export interface SpotSubscriber {
  id: number | null
  email: string
  subscriber_status: string
}

interface SpotRequestBase {
  request_reference: string
  fire_number: string[]
  fire_centre: number
  status: string
  request_frequency: string[]
  request_type: string
  aspect: string
  elevation: number
  geographic_description: string
  additional_information?: string
  latitude: number
  longitude: number
  requested_at: string
  start_at: string
  end_at: string
  subscribers: SpotSubscriber[]
}

export interface SpotRequestInput extends SpotRequestBase {
  id: number | null
}

export interface SpotRequestOutput extends SpotRequestBase {
  id: number
  requestor_name: string
  requestor_idir: string
  requestor_email: string
}

export interface SpotRequestResponse {
  spot_request: SpotRequestOutput
}

export interface SpotRequestsResponse {
  spot_requests: SpotRequestOutput[]
}

const spotRequestTypeMap: Record<SpotRequestFormData['forecastType'], string> = {
  MINI_SPOT: 'Mini',
  FULL_SPOT: 'Full'
}

const createSpotRequestReference = () => `WPS-${new Date().toISOString()}`

const toStartOfDayISO = (dateTime: SpotRequestFormData['forecastStartDate']) => dateTime.startOf('day').toISO()!

const toEndOfDayISO = (dateTime: SpotRequestFormData['forecastEndDate']) =>
  dateTime.set({ hour: 23, minute: 59, second: 0, millisecond: 0 }).toISO()!

const marshalFormDataToSpotRequestInput = (formData: SpotRequestFormData): SpotRequestInput => {
  return {
    id: null,
    request_reference: createSpotRequestReference(),
    fire_number: [formData.fireNumber],
    fire_centre: formData.fireCentreId,
    status: 'Requested',
    request_frequency: formData.requestedFrequency,
    request_type: spotRequestTypeMap[formData.forecastType],
    aspect: formData.slopeAspect,
    elevation: Number(formData.elevation),
    geographic_description: formData.geographicDescription,
    additional_information: formData.additionalInformation || undefined,
    latitude: formData.location.latitude,
    longitude: formData.location.longitude,
    requested_at: new Date().toISOString(),
    start_at: toStartOfDayISO(formData.forecastStartDate),
    end_at: toEndOfDayISO(formData.forecastEndDate),
    subscribers: formData.emailDistributionList.map(email => ({
      id: null,
      email,
      subscriber_status: 'active'
    }))
  }
}

export const postSpotForecast = async (formData: SpotFormData): Promise<SpotForecastResponse> => {
  const spotForecastInput = marshalFormDataToSpotForecastInput(formData)
  const url = '/smurfi/forecast'
  const { data } = await axios.post(url, {
    spot_forecast: spotForecastInput
  })
  return data
}

export const postSpotRequest = async (formData: SpotRequestFormData): Promise<SpotRequestResponse> => {
  const spotRequestInput = marshalFormDataToSpotRequestInput(formData)
  const url = '/smurfi/spot_request'
  const { data } = await axios.post(url, spotRequestInput)
  return data
}

export async function getSpotAdminRows(): Promise<SpotAdminRowResponse> {
  const url = '/smurfi/admin/'
  const { data } = await axios.get(url)
  return data
}

export async function getSpotPDF(spotId: number): Promise<Blob> {
  const url = `/smurfi/pdf/${spotId}`
  const response = await axios.get(url, { responseType: 'blob' })
  return response.data
}

export interface SubscribeResponse {
  subscriber_status: string
}

export interface SubscriptionsResponse {
  spot_request_ids: number[]
}

export async function subscribeToSpot(spotRequestId: number): Promise<SubscribeResponse> {
  const { data } = await axios.post(`/smurfi/spots/${spotRequestId}/subscribe`)
  return data
}

export async function unsubscribeFromSpot(spotRequestId: number): Promise<void> {
  await axios.delete(`/smurfi/spots/${spotRequestId}/subscribe`)
}

export async function getSubscriptions(): Promise<SubscriptionsResponse> {
  const { data } = await axios.get('/smurfi/subscriptions')
  return data
}

export const getSpotRequests = async (): Promise<SpotRequestsResponse> => {
  const url = '/smurfi/spot_requests'
  const { data } = await axios.get(url)
  return data
}
