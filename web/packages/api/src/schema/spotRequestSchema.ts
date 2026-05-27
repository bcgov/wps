import { z } from 'zod'
import { DateTime } from 'luxon'

export const spotForecastTypes = ['Mini', 'Full'] as const

export const requestedFrequencyOptions = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday'
] as const

const requiredString = (message = 'Required') => z.string().trim().min(1, message)
const optionalString = () => z.string().trim().optional()

const validDateTime = (message = 'Invalid date/time') =>
  z.custom<DateTime>((val): val is DateTime => DateTime.isDateTime(val) && val.isValid, {
    message
  })

const requiredCoordinate = z.object({
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180)
})
type SpotRequestCoordinate = z.infer<typeof requiredCoordinate>

export const spotRequestSchema = z
  .object({
    fireNumbers: z.array(requiredString()).min(1, 'At least one fire number is required'),
    fireCentreId: z.number().int().positive('Required'),
    forecastStartDate: validDateTime(),
    forecastEndDate: validDateTime(),
    forecastType: z.enum(spotForecastTypes),
    emailDistributionList: z.array(z.string().email('Invalid email')).default([]),
    distributionGroupIds: z.array(z.number().int()).default([]),
    requestedFrequency: z.array(z.enum(requestedFrequencyOptions)).min(1, 'Select at least one day'),
    location: requiredCoordinate
      .nullable()
      .refine(value => value !== null, {
        message: 'Select a location',
        path: ['latitude']
      })
      .transform(value => value as SpotRequestCoordinate),
    geographicDescription: requiredString(),
    slopeAspect: optionalString(),
    elevation: optionalString()
      .refine(value => !value || Number.isFinite(Number(value)), 'Elevation must be a number')
      .refine(value => !value || Number.isInteger(Number(value)), 'Elevation must be a whole number'),
    additionalInformation: z.string().optional()
  })
  .refine(data => data.forecastEndDate.toMillis() >= data.forecastStartDate.toMillis(), {
    message: 'Forecast end date must be after the start date',
    path: ['forecastEndDate']
  })
  .refine(data => data.emailDistributionList.length > 0 || data.distributionGroupIds.length > 0, {
    message: 'At least one email or distribution group is required',
    path: ['emailDistributionList']
  })

export type SpotRequestFormValues = z.input<typeof spotRequestSchema>
export type SpotRequestFormData = z.output<typeof spotRequestSchema>
