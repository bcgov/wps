import { DateTime } from 'luxon'
import { RepresentativeStation } from '@/features/smurfi/interfaces'
import { SpotForecastOutput } from '@wps/api/SMURFIAPI'

export const TIMEZONE = 'America/Vancouver'
const forecastDateTimeFormat = 'yyyy-MM-dd HH:mm'

export const formatDateTime = (iso: string): string => {
  const dt = DateTime.fromISO(iso).setZone(TIMEZONE)
  return dt.isValid ? `${dt.toFormat('HH:mm')} ${dt.offsetNameShort} ${dt.toFormat('EEE, MMM d, yyyy')}` : iso
}

export const toForecastDateTimeString = (value: string): string => {
  const dateTime = DateTime.fromISO(value).setZone(TIMEZONE)
  return dateTime.isValid ? dateTime.toFormat(forecastDateTimeFormat) : value
}

export const formatFireNumbers = (fireNumbers: string[] | null | undefined): string => fireNumbers?.join(', ') ?? ''

export const getEmptyFireSizes = (fireNumbers: string[] | null | undefined): string[] =>
  fireNumbers?.map(() => '') ?? []

export const formatStationsStr = (stations: RepresentativeStation[]): string =>
  stations.length > 0 ? stations.map(s => s.name + (s.elevation == null ? '' : ` (${s.elevation}m)`)).join(', ') : '—'

export const getMostRecentForecast = (forecasts: SpotForecastOutput[]): SpotForecastOutput | undefined =>
  forecasts.reduce<SpotForecastOutput | undefined>((mostRecent, forecast) => {
    if (!mostRecent) {
      return forecast
    }

    return Date.parse(forecast.created_at) > Date.parse(mostRecent.created_at) ? forecast : mostRecent
  }, undefined)
