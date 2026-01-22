import axios from '@/api/axios'
import { FetchChefsFormResponse, SpotAdminRowResponse } from '@/features/smurfi/interfaces'
import { FormData } from '@/features/smurfi/schemas/spotForecastSchema'

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

const marshalFormDataToSpotForecastInput = (formData: FormData): SpotForecastInput => {
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

export const postSpotForecast = async (formData: FormData): Promise<SpotForecastResponse> => {
  const spotForecastInput = marshalFormDataToSpotForecastInput(formData)
  const url = '/smurfi/forecast'
  const { data } = await axios.post(url, {
    spot_forecast: spotForecastInput
  })
  return data
}

export async function getSpotAdminRows(): Promise<SpotAdminRowResponse> {
  const url = '/smurfi/admin/'
  const { data } = await axios.get(url)
  return data
}

export async function runFetchChefsForms(): Promise<FetchChefsFormResponse> {
  const url = 'smurfi/pull_from_chefs'
  const { data } = await axios.get(url)
  return data
}
