import axios from '@/api/axios'
import { FetchChefsFormResponse, SpotAdminRowResponse } from '@/features/smurfi/interfaces'
import { DateTime } from 'luxon'

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
const mock_data = {
  spot_id: 123,
  fire_number: 'C12345',
  requested_by: 'Jane Doe',
  forecaster: 'John Smith',
  latitude: '50.1234',
  longitude: '-120.5678',
  elevation: '800',
  representative_weather_stations: ['StationA', 'StationB'],
  forecaster_email: 'john.smith@gov.bc.ca',
  forecaster_phone: '555-123-4567',
  additional_fire_numbers: ['C54321', 'C67890'],
  geographic_area_name: 'Cariboo',
  fire_centre: 'Kamloops',
  fire_size: '1200.5',
  slope: '15',
  aspect: 'Southwest',
  valley: 'Fraser',
  synopsis: 'A ridge of high pressure remains in place.',
  inversion_and_venting: 'Inversion expected to break by noon.',
  outlook: 'Cooler and wetter conditions expected tomorrow.',
  confidence: 'High',
  general_forecasts: [
    {
      period: 'Afternoon',
      temperature: 22.5,
      relative_humidity: 35,
      conditions: 'Sunny'
    },
    {
      period: 'Tonight',
      temperature: 12.3,
      relative_humidity: 60,
      conditions: 'Clear'
    }
  ],
  forecasts: [
    {
      forecast_time: '2026-01-22T14:00:00Z',
      temperature: 21.0,
      relative_humidity: 40,
      wind: 'SW 10 km/h',
      probability_of_precipitation: 10,
      precipitation_amount: 0
    },
    {
      forecast_time: '2026-01-22T20:00:00Z',
      temperature: 16.5,
      relative_humidity: 55,
      wind: 'Calm',
      probability_of_precipitation: 20,
      precipitation_amount: 0.2
    }
  ]
}

function mapBackendToFormData(data: any): any {
  const general = data.general_forecasts || []
  return {
    issuedDate: DateTime.now(), // or DateTime.fromISO(data.issuedDate) if available
    expiryDate: DateTime.now().plus({ days: 1 }), // or DateTime.fromISO(data.expiryDate)
    fireProj: data.fire_number || '',
    requestBy: data.requested_by || '',
    forecastBy: data.forecaster || '',
    email: data.forecaster_email || '',
    phone: data.forecaster_phone || '',
    city: data.geographic_area_name || '',
    stns: (data.representative_weather_stations || []).map(Number).filter(n => !isNaN(n)),
    latitude: data.latitude?.toString() || '',
    longitude: data.longitude?.toString() || '',
    slopeAspect: data.aspect || '',
    valley: data.valley || '',
    elevation: data.elevation?.toString() || '',
    size: data.fire_size?.toString() || '',
    synopsis: data.synopsis || '',
    afternoonForecast: general[0]
      ? {
          description: general[0].conditions || '',
          maxTemp: general[0].temperature ?? undefined,
          minRh: general[0].relative_humidity ?? undefined
        }
      : undefined,
    tonightForecast: general[1]
      ? {
          description: general[1].conditions || '',
          minTemp: general[1].temperature ?? undefined,
          maxRh: general[1].relative_humidity ?? undefined
        }
      : undefined,
    tomorrowForecast: general[2]
      ? {
          description: general[2].conditions || '',
          maxTemp: general[2].temperature ?? undefined,
          minRh: general[2].relative_humidity ?? undefined
        }
      : undefined,
    weatherData: (data.forecasts || []).map((f: any) => ({
      dateTime: f.forecast_time || '',
      temp: f.temperature?.toString() || '',
      rh: f.relative_humidity?.toString() || '',
      windSpeed: f.wind || '',
      windGust: '', // Not present in backend, leave blank or map if available
      windDirection: '', // Not present in backend, leave blank or map if available
      rain: f.precipitation_amount?.toString() || '',
      chanceRain: f.probability_of_precipitation?.toString() || ''
    })),
    inversionVenting: data.inversion_and_venting || '',
    outlook: data.outlook || '',
    confidenceDiscussion: data.confidence || ''
  }
}

export async function getForecastPageData(spotRequestId: number): Promise<any> {
  // const url = `/smurfi/forecast_page_data/${spotRequestId}`
  // const { data } = await axios.get(url)
  return mapBackendToFormData(mock_data)
}
