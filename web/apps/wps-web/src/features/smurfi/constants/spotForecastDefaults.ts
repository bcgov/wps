import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import { DateTime } from 'luxon'

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

export const defaultWeatherRows: SpotFormData['weatherData'] = defaultDateTimes.map(dt => ({
  id: null,
  dateTime: dt.toFormat('yyyy-MM-dd HH:mm'),
  temp: '',
  rh: '',
  wind: '',
  rain: '',
  chanceRain: ''
}))

export const getDefaultValues = (): Partial<SpotFormData> => ({
  issuedDate: DateTime.now().setZone('America/Vancouver'),
  expiryDate: DateTime.now().setZone('America/Vancouver').plus({ days: 1 }).endOf('day'),
  fireProj: '',
  requestBy: '',
  stns: [],
  latitude: '',
  longitude: '',
  slopeAspect: '',
  valley: '',
  elevation: '',
  size: '',
  synopsis: '',
  afternoonForecast: {
    description: '',
    maxTemp: undefined,
    minRh: undefined
  },
  tonightForecast: {
    description: '',
    minTemp: undefined,
    maxRh: undefined
  },
  tomorrowForecast: {
    description: '',
    maxTemp: undefined,
    minRh: undefined
  },
  weatherData: defaultWeatherRows,
  inversionVenting: '',
  outlook: '',
  confidenceDiscussion: ''
})
