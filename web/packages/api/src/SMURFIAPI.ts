import axios from './axios'
import { SpotFormData } from './schema/spotForecastSchema'
import { SpotRequestFormData } from './schema/spotRequestSchema'
import { DateTime } from 'luxon'

export enum SpotForecastStatus {
  NEW = 'New',
  ACTIVE = 'Active',
  INACTIVE = 'Inactive',
  PAUSED = 'Paused',
  ARCHIVED = 'Archived'
}

export interface SpotAdminRow {
  id: number
  spot_id: number
  fire_id: string
  forecaster: string
  fire_centre: string
  status: SpotForecastStatus
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
  id: number | null
  spot_request_id: number
  forecaster_name: string
  forecaster_email: string
  forecaster_phone?: string
  synopsis?: string
  inversion_and_venting?: string
  outlook?: string
  confidence?: string
  fire_size?: number | null
  representative_station_codes?: number[]
  for_date?: string
  descriptive_weather: {
    id: number | null
    period: 'Today' | 'Tonight' | 'Tomorrow'
    temperature: number | null
    relative_humidity: number | null
    conditions: string | null
  }[]
  tabular_weather: {
    id: number | null
    forecast_time: string
    temperature: number | null
    relative_humidity: number | null
    wind: string | null
    probability_of_precipitation: number | null
    precipitation_amount: number | null
  }[]
}

const toNullableNumber = (value: string | undefined): number | null => {
  if (value === undefined || value.trim() === '' || value.trim() === '-') {
    return null
  }
  const numberValue = Number(value)
  return Number.isFinite(numberValue) ? numberValue : null
}

const toForecastTimeISO = (dateTime: string) => {
  const parsedDateTime = DateTime.fromFormat(dateTime, 'yyyy-MM-dd HH:mm', { zone: 'America/Vancouver' })
  return parsedDateTime.isValid ? parsedDateTime.toISO()! : dateTime
}

const marshalFormDataToSpotForecastInput = (formData: SpotFormData, spotRequestId: number): SpotForecastInput => {
  const descriptiveWeather: SpotForecastInput['descriptive_weather'] = [
    formData.afternoonForecast
      ? {
          id: null,
          period: 'Today' as const,
          temperature: formData.afternoonForecast.maxTemp ?? null,
          relative_humidity: formData.afternoonForecast.minRh ?? null,
          conditions: formData.afternoonForecast.description || null
        }
      : undefined,
    formData.tonightForecast
      ? {
          id: null,
          period: 'Tonight' as const,
          temperature: formData.tonightForecast.minTemp ?? null,
          relative_humidity: formData.tonightForecast.maxRh ?? null,
          conditions: formData.tonightForecast.description || null
        }
      : undefined,
    formData.tomorrowForecast
      ? {
          id: null,
          period: 'Tomorrow' as const,
          temperature: formData.tomorrowForecast.maxTemp ?? null,
          relative_humidity: formData.tomorrowForecast.minRh ?? null,
          conditions: formData.tomorrowForecast.description || null
        }
      : undefined
  ].filter(weather => weather !== undefined)

  return {
    id: null,
    spot_request_id: spotRequestId,
    forecaster_name: formData.forecastBy,
    forecaster_email: formData.email,
    forecaster_phone: formData.phone,
    synopsis: formData.synopsis,
    inversion_and_venting: formData.inversionVenting,
    outlook: formData.outlook,
    confidence: formData.confidenceDiscussion,
    fire_size: toNullableNumber(formData.size),
    representative_station_codes: formData.stns,
    for_date: formData.issuedDate.toISO()!,
    descriptive_weather: descriptiveWeather,
    tabular_weather: formData.weatherData.map(row => ({
      id: null,
      forecast_time: toForecastTimeISO(row.dateTime),
      temperature: toNullableNumber(row.temp),
      relative_humidity: toNullableNumber(row.rh),
      wind: row.wind || null,
      probability_of_precipitation: toNullableNumber(row.chanceRain),
      precipitation_amount: toNullableNumber(row.rain)
    }))
  }
}

export interface SpotForecastOutput extends Omit<SpotForecastInput, 'id'> {
  id: number
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

export const postSpotForecast = async (
  formData: SpotFormData,
  spotRequestId: number
): Promise<SpotForecastResponse> => {
  const spotForecastInput = marshalFormDataToSpotForecastInput(formData, spotRequestId)
  const url = '/smurfi/spot_forecast'
  const { data } = await axios.post(url, spotForecastInput)
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
