import axios from './axios'
import { SpotFormData } from './schema/spotForecastSchema'
import { SpotRequestFormData } from './schema/spotRequestSchema'
import { DateTime } from 'luxon'

const COMPASS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'] as const

const degreesToCompass = (degrees: number): string => COMPASS[Math.round((((degrees % 360) + 360) % 360) / 45) % 8]

export enum SpotRequestStatus {
  REQUESTED = 'Requested',
  STARTED = 'Started',
  SUSPENDED = 'Suspended',
  COMPLETE = 'Complete',
  ARCHIVED = 'Archived'
}

export type SpotForecastType = 'Mini' | 'Full'

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
  spot_request?: SpotRequestOutput
}

interface SpotDescriptiveWeatherInput {
  period: 'Today' | 'Tonight' | 'Tomorrow'
  temperature: number | null
  relative_humidity: number | null
  conditions: string | null
}

interface SpotTabularWeatherInput {
  forecast_time: string
  temperature: number | null
  relative_humidity: number | null
  wind: string | null
  probability_of_precipitation: number | null
  precipitation_amount: number | null
}

export interface SpotForecastInput {
  spot_request_base_id: number
  spot_request_instance: SpotRequestInstanceInput
  forecast_type: SpotForecastType
  issued_at: string
  expires_at?: string | null
  synopsis?: string
  inversion_and_venting?: string
  outlook?: string
  confidence?: string
  fire_size?: (number | null)[] | null
  representative_station_codes?: number[]
  descriptive_weather: SpotDescriptiveWeatherInput[]
  tabular_weather: SpotTabularWeatherInput[]
}

export interface SpotDescriptiveWeatherOutput extends SpotDescriptiveWeatherInput {
  id: number
}

interface SpotTabularWeatherOutput extends SpotTabularWeatherInput {
  id: number
}

export interface SpotForecastOutput extends Omit<SpotForecastInput, 'descriptive_weather' | 'tabular_weather'> {
  id: number
  spot_request_instance_id: number
  spot_request_instance: SpotRequestInstanceOutput
  created_at: string
  forecaster_name: string
  forecaster_email: string
  forecaster_phone?: string | null
  descriptive_weather: SpotDescriptiveWeatherOutput[]
  tabular_weather: SpotTabularWeatherOutput[]
}

const toNullableNumber = (value: string | undefined): number | null => {
  if (value === undefined || value.trim() === '' || value.trim() === '-') {
    return null
  }
  const numberValue = Number(value)
  return Number.isFinite(numberValue) ? numberValue : null
}

const toNullableNumberList = (values: (string | undefined)[] | undefined): (number | null)[] | null => {
  if (!values?.length) {
    return null
  }

  const numberValues = values.map(toNullableNumber)
  return numberValues.some(value => value !== null) ? numberValues : null
}

const toNullableInteger = (value: string | undefined): number | null => {
  const numberValue = toNullableNumber(value)
  return numberValue === null ? null : Math.trunc(numberValue)
}

const toForecastTimeISO = (dateTime: string) => {
  const parsedDateTime = DateTime.fromFormat(dateTime, 'yyyy-MM-dd HH:mm', { zone: 'America/Vancouver' })
  return parsedDateTime.isValid ? parsedDateTime.toISO()! : dateTime
}

const marshalFormDataToSpotForecastInput = (
  formData: SpotFormData,
  spotRequestId: number,
  forecastType: SpotForecastType
): SpotForecastInput => {
  const descriptiveWeather: SpotForecastInput['descriptive_weather'] = [
    formData.afternoonForecast
      ? {
          period: 'Today' as const,
          temperature: formData.afternoonForecast.maxTemp ?? null,
          relative_humidity: formData.afternoonForecast.minRh ?? null,
          conditions: formData.afternoonForecast.description || null
        }
      : undefined,
    formData.tonightForecast
      ? {
          period: 'Tonight' as const,
          temperature: formData.tonightForecast.minTemp ?? null,
          relative_humidity: formData.tonightForecast.maxRh ?? null,
          conditions: formData.tonightForecast.description || null
        }
      : undefined,
    formData.tomorrowForecast
      ? {
          period: 'Tomorrow' as const,
          temperature: formData.tomorrowForecast.maxTemp ?? null,
          relative_humidity: formData.tomorrowForecast.minRh ?? null,
          conditions: formData.tomorrowForecast.description || null
        }
      : undefined
  ].filter(weather => weather !== undefined)

  return {
    spot_request_base_id: spotRequestId,
    forecast_type: forecastType,
    spot_request_instance: {
      geographic_description: formData.geographicDescription,
      aspect: formData.slopeAspect,
      elevation: toNullableInteger(formData.elevation),
      valley: formData.valley || null,
      latitude: Number(formData.latitude),
      longitude: Number(formData.longitude)
    },
    synopsis: formData.synopsis,
    inversion_and_venting: formData.inversionVenting,
    outlook: formData.outlook,
    confidence: formData.confidenceDiscussion,
    fire_size: toNullableNumberList(formData.fireSizes),
    representative_station_codes: formData.stns,
    issued_at: formData.issuedDate.toISO()!,
    expires_at: formData.expiryDate.toISO(),
    descriptive_weather: descriptiveWeather,
    tabular_weather: formData.weatherData.map(row => ({
      forecast_time: toForecastTimeISO(row.dateTime),
      temperature: toNullableNumber(row.temp),
      relative_humidity: toNullableNumber(row.rh),
      wind: row.wind || null,
      probability_of_precipitation: toNullableNumber(row.chanceRain),
      precipitation_amount: toNullableNumber(row.rain)
    }))
  }
}

export interface SpotForecastResponse {
  spot_forecast: SpotForecastOutput
}

export interface SpotForecastsResponse {
  spot_forecasts: SpotForecastOutput[]
}

export interface SpotSubscriber {
  id: number | null
  email: string
  subscriber_status: string
}

export interface SpotLatestForecast {
  id: number
  created_at: string
  issued_at: string
  expires_at?: string | null
  forecast_end_at?: string | null
  forecaster_name?: string | null
}

export interface SpotRequestInstanceInput {
  geographic_description: string
  aspect?: string | null
  elevation?: number | null
  valley?: string | null
  latitude: number
  longitude: number
}

export interface SpotRequestInstanceOutput extends SpotRequestInstanceInput {
  id: number
}

interface SpotRequestFields {
  request_reference: string
  fire_number: string[]
  fire_centre: number
  status: SpotRequestStatus
  request_frequency: string[]
  request_type: string
  additional_information?: string
  requested_at: string
  start_at: string
  end_at: string
  subscribers: SpotSubscriber[]
  latest_forecast?: SpotLatestForecast | null
}

export interface SpotRequestInput extends SpotRequestFields {
  id: number | null
  initial_instance: SpotRequestInstanceInput
}

export interface SpotRequestOutput extends SpotRequestFields {
  id: number
  initial_instance: SpotRequestInstanceOutput
  current_instance: SpotRequestInstanceOutput
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

const createSpotRequestReference = () => `WPS-${new Date().toISOString()}`

const toStartOfDayISO = (dateTime: SpotRequestFormData['forecastStartDate']) => dateTime.startOf('day').toISO()!

const toEndOfDayISO = (dateTime: SpotRequestFormData['forecastEndDate']) =>
  dateTime.set({ hour: 23, minute: 59, second: 0, millisecond: 0 }).toISO()!

const marshalFormDataToSpotRequestInput = (formData: SpotRequestFormData): SpotRequestInput => {
  return {
    id: null,
    request_reference: createSpotRequestReference(),
    fire_number: formData.fireNumbers,
    fire_centre: formData.fireCentreId,
    status: SpotRequestStatus.REQUESTED,
    request_frequency: formData.requestedFrequency,
    request_type: formData.forecastType,
    additional_information: formData.additionalInformation || undefined,
    initial_instance: {
      geographic_description: formData.geographicDescription,
      aspect: formData.slopeAspect || null,
      elevation: toNullableInteger(formData.elevation),
      valley: null,
      latitude: formData.location.latitude,
      longitude: formData.location.longitude
    },
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

export const postSpotForecast = async (
  formData: SpotFormData,
  spotRequestId: number,
  forecastType: SpotForecastType
): Promise<SpotForecastResponse> => {
  const spotForecastInput = marshalFormDataToSpotForecastInput(formData, spotRequestId, forecastType)
  const url = '/smurfi/spot_forecast'
  const { data } = await axios.post(url, spotForecastInput)
  return data
}

export const getSpotForecasts = async (spotRequestId: number): Promise<SpotForecastsResponse> => {
  const url = `/smurfi/spot_requests/${spotRequestId}/spot_forecasts`
  const { data } = await axios.get(url)
  return data
}

export const postSpotRequest = async (formData: SpotRequestFormData): Promise<SpotRequestResponse> => {
  const spotRequestInput = marshalFormDataToSpotRequestInput(formData)
  const url = '/smurfi/spot_request'
  const { data } = await axios.post(url, spotRequestInput)
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
