import { z } from 'zod'
import { DateTime } from 'luxon'

export const createSchema = (isMini: boolean) => {
  const weatherRowSchema = z.object({
    dateTime: z.string().min(1, 'Date/Time required'),
    temp: z
      .string()
      .optional()
      .refine(val => !val || !Number.isNaN(val), 'Must be a number'),
    rh: z
      .string()
      .optional()
      .refine(val => {
        if (!val) return true
        const num = Number(val)
        return !Number.isNaN(num) && num >= 0 && num <= 100
      }, 'RH must be a number between 0 and 100'),
    windSpeed: z.string().optional(),
    windGust: z.string().optional(),
    windDirection: z
      .string()
      .optional()
      .refine(val => {
        if (!val) return true
        const num = Number(val)
        return !isNaN(num) && num >= 0 && num <= 359
      }, 'Wind direction must be a number between 0 and 359'),
    rain: z.string().optional(),
    chanceRain: z.string().optional()
  })

  return z.object({
    issuedDate: z.custom<DateTime>((val): val is DateTime => DateTime.isDateTime(val) && val.isValid, {
      message: 'Invalid date/time'
    }),
    expiryDate: z.custom<DateTime>((val): val is DateTime => DateTime.isDateTime(val) && val.isValid, {
      message: 'Invalid date/time'
    }),
    fireProj: z.string().min(1, 'Required'),
    requestBy: z.string().refine(val => val.length > 0, 'Required'),
    forecastBy: z.string().refine(val => val.length > 0, 'Required'),
    email: z.string().email('Invalid email'),
    phone: z.string().refine(val => val.length > 0, 'Required'),
    city: z.string().refine(val => val.length > 0, 'Required'),
    stns: z.array(z.number()).optional(),
    coordinates: z.string().optional(),
    slopeAspect: z.string().optional(),
    valley: z.string().optional(),
    elevation: z.string().optional(),
    size: z.string().optional(),
    synopsis: z.string().min(1, 'Required'),
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
    inversionVenting: z.string().min(1, 'Required'),
    outlook: z.string().refine(val => isMini || val.length > 0, isMini ? undefined : 'Required'),
    confidenceDiscussion: z.string().min(1, 'Required')
  })
}

export type FormData = z.infer<ReturnType<typeof createSchema>>
