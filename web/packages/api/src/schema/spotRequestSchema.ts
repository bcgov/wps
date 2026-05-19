import { z } from 'zod'
import { DateTime } from 'luxon'

export const spotForecastTypes = ['MINI_SPOT', 'FULL_SPOT'] as const

export const requestedFrequencyOptions = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday'
] as const

export const slopeAspectOptions = [
  'North',
  'Northeast',
  'East',
  'Southeast',
  'South',
  'Southwest',
  'West',
  'Northwest',
  'Flat/Variable'
] as const

const requiredString = (message = 'Required') => z.string().trim().min(1, message)

const validDateTime = (message = 'Invalid date/time') =>
  z.custom<DateTime>((val): val is DateTime => DateTime.isDateTime(val) && val.isValid, {
    message
  })

const requiredCoordinate = z.object({
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180)
})

export const spotRequestSchema = z
  .object({
    fireNumber: requiredString(),
    forecastStartDate: validDateTime(),
    forecastEndDate: validDateTime(),
    forecastType: z.enum(spotForecastTypes),
    emailDistributionList: z.array(z.string().email('Invalid email')).min(1, 'At least one email is required'),
    requestedFrequency: z.array(z.enum(requestedFrequencyOptions)).min(1, 'Select at least one day'),
    location: requiredCoordinate.nullable().refine(value => value !== null, {
      message: 'Select a location',
      path: ['latitude']
    }),
    geographicDescription: requiredString(),
    slopeAspect: z.enum(slopeAspectOptions, {
      errorMap: () => ({ message: 'Required' })
    }),
    elevation: requiredString().refine(value => Number.isFinite(Number(value)), 'Elevation must be a number'),
    additionalInformation: z.string().optional()
  })
  .refine(data => data.forecastEndDate.toMillis() >= data.forecastStartDate.toMillis(), {
    message: 'Forecast end date must be after the start date',
    path: ['forecastEndDate']
  })

export type SpotRequestFormValues = z.input<typeof spotRequestSchema>
export type SpotRequestFormData = z.output<typeof spotRequestSchema>
