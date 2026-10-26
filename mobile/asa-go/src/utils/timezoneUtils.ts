import { DateTime } from 'luxon'
import { ASA_GO_TIMEZONE } from '@/utils/constants'

// BC moved to permanent Pacific Time (UTC-7) on Nov 1, 2026; it's labelled PCT from then on instead of PDT.
const PCT_START_DATE = '2026-11-01'

/**
 * Label for UTC-7 BC time on the given ISO date. We don't rely on the device for this as it may be outside BC, in a
 * Mountain time part of BC, or have timezone data that predates BC's switch to permanent Pacific Time.
 */
export const getBCTimezoneLabel = (isoDate: string): string => (isoDate >= PCT_START_DATE ? 'PCT' : 'PDT')

export const formatDatetimeInBCTime = (dt: DateTime): string => {
  const bcTime = dt.setZone(ASA_GO_TIMEZONE)
  const formatted = bcTime.toLocaleString({ ...DateTime.DATETIME_FULL, timeZoneName: undefined })
  return `${formatted} ${getBCTimezoneLabel(bcTime.toISODate() ?? '')}`
}
