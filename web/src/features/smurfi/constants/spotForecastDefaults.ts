import { DateTime } from 'luxon'
import type { FormData } from '@/features/smurfi/schemas/spotForecastSchema'

export const defaultDateTimes = [
  DateTime.now().setZone('America/Vancouver').set({ hour: 16, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').set({ hour: 19, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').set({ hour: 0, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').plus({ days: 1 }).set({ hour: 10, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').plus({ days: 1 }).set({ hour: 13, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').plus({ days: 1 }).set({ hour: 16, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').plus({ days: 1 }).set({ hour: 19, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').plus({ days: 1 }).set({ hour: 0, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').plus({ days: 2 }).set({ hour: 16, minute: 0 })
]

export const defaultWeatherRows: FormData['weatherData'] = defaultDateTimes.map(dt => ({
  dateTime: dt.toFormat('yyyy-MM-dd HH:mm'),
  temp: '',
  rh: '',
  windSpeed: '',
  windGust: '',
  windDirection: '',
  rain: '',
  chanceRain: ''
}))

export const getDefaultValues = (user: { name: string; email: string; phone: string }): Partial<FormData> => ({
  issuedDate: DateTime.now().setZone('America/Vancouver'),
  expiryDate: DateTime.now().setZone('America/Vancouver').plus({ days: 1 }).endOf('day'),
  fireProj: 'K00000',
  requestBy: 'Marsha Mellow',
  forecastBy: user.name,
  email: user.email,
  phone: user.phone,
  city: 'Kamloops',
  stns: [],
  coordinates: '50.612, -120.20088',
  slopeAspect: 'South',
  valley: 'W to E',
  elevation: '545',
  size: '5 to 20',
  synopsis: '',
  afternoonForecast: {
    description: 'Mainly sunny in the morning then increasing afternoon cloud.',
    maxTemp: 11,
    minRh: 40
  },
  tonightForecast: {
    description: 'Mainly clear.',
    minTemp: -2,
    maxRh: 90
  },
  tomorrowForecast: {
    description: 'Cloudy.',
    maxTemp: 12,
    minRh: 40
  },
  weatherData: defaultWeatherRows,
  inversionVenting: '',
  outlook: '',
  confidenceDiscussion: ''
})
