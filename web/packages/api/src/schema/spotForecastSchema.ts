import { z } from 'zod'
import { DateTime } from 'luxon'

const requiredString = (message = 'Required') => z.string().trim().min(1, message)
const tabularWeatherDateTimeFormat = 'yyyy-MM-dd HH:mm'

const isOptionalNumber = (val: string | undefined) => {
  if (val === undefined || val.trim() === '') {
    return true
  }

  return Number.isFinite(Number(val))
}

const optionalNumericString = (message: string, isInRange: (value: number) => boolean = () => true) =>
  z
    .string()
    .optional()
    .refine(val => isOptionalNumber(val) && (val === undefined || val.trim() === '' || isInRange(Number(val))), message)

const requiredNumericString = (rangeMessage: string, isInRange: (value: number) => boolean) =>
  requiredString().refine(val => {
    const num = Number(val)
    return Number.isFinite(num) && isInRange(num)
  }, rangeMessage)

const requiredWholeNumberString = (numberMessage: string, integerMessage: string) =>
  requiredString()
    .refine(value => Number.isFinite(Number(value)), numberMessage)
    .refine(value => Number.isInteger(Number(value)), integerMessage)

const requiredTabularWeatherDateTime = () =>
  requiredString('Date/Time required').refine(value => {
    const parsedDateTime = DateTime.fromFormat(value, tabularWeatherDateTimeFormat, { zone: 'America/Vancouver' })
    return parsedDateTime.isValid && parsedDateTime.toFormat(tabularWeatherDateTimeFormat) === value
  }, `Use format ${tabularWeatherDateTimeFormat}`)

export const createSchema = (isMini: boolean) => {
  const weatherRowSchema = z.object({
    dateTime: requiredTabularWeatherDateTime(),
    temp: optionalNumericString('Must be a number'),
    rh: optionalNumericString('RH must be a number between 0 and 100', num => num >= 0 && num <= 100),
    wind: z.string().optional(),
    rain: optionalNumericString('Must be a number'),
    chanceRain: optionalNumericString('Must be a number')
  })

  return z.object({
    issuedDate: z.custom<DateTime>((val): val is DateTime => DateTime.isDateTime(val) && val.isValid, {
      message: 'Invalid date/time'
    }),
    expiryDate: z.custom<DateTime>((val): val is DateTime => DateTime.isDateTime(val) && val.isValid, {
      message: 'Invalid date/time'
    }),
    fireProj: requiredString(),
    requestBy: requiredString(),
    stns: z.array(z.number()).optional(),
    latitude: requiredNumericString('Latitude must be a number between -90 and 90', num => num >= -90 && num <= 90),
    longitude: requiredNumericString(
      'Longitude must be a negative number between -180 and 0',
      num => num >= -180 && num <= 0
    ),
    geographicDescription: requiredString(),
    slopeAspect: requiredString(),
    valley: z.string().optional(),
    elevation: requiredWholeNumberString('Elevation must be a number', 'Elevation must be a whole number'),
    fireSizes: z.array(optionalNumericString('Must be a number')).optional(),
    synopsis: requiredString(),
    afternoonForecast: z
      .object({
        description: z.string().optional(),
        maxTemp: z.number().optional(),
        minRh: z.number().min(0).max(100).optional()
      })
      .optional(),
    tonightForecast: z
      .object({
        description: z.string().optional(),
        minTemp: z.number().optional(),
        maxRh: z.number().min(0).max(100).optional()
      })
      .optional(),
    tomorrowForecast: z
      .object({
        description: z.string().optional(),
        maxTemp: z.number().optional(),
        minRh: z.number().min(0).max(100).optional()
      })
      .optional(),
    weatherData: z
      .array(weatherRowSchema)
      .min(isMini ? 0 : 1, isMini ? undefined : 'At least one weather entry required'),
    inversionVenting: requiredString(),
    outlook: isMini ? z.string().optional() : requiredString(),
    confidenceDiscussion: requiredString()
  })
}

export type SpotFormData = z.infer<ReturnType<typeof createSchema>>
