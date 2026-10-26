import { DateTime } from 'luxon'

// BC moved to permanent Pacific Time (UTC-7) on Nov 1, 2026; it's labelled PCT from then on instead of PDT.
const PCT_START_DATE = '2026-11-01'

/**
 * Label for UTC-7 BC time on the given ISO date. We don't rely on the device for this as it may be outside BC, in a
 * Mountain time part of BC, or have timezone data that predates BC's switch to permanent Pacific Time.
 */
export const getBCTimezoneLabel = (isoDate: string): string => (isoDate >= PCT_START_DATE ? 'PCT' : 'PDT')

const PACIFIC_ZONES = new Set(['America/Vancouver', 'Canada/Pacific'])

/**
 * Formats a datetime in its own (usually the device's) timezone. Timezone data doesn't have a PCT abbreviation,
 * so Pacific times from Nov 1, 2026 are labelled PCT here instead of the PDT/MST the device would print. Devices
 * whose timezone data predates the switch still show UTC-8, so they keep their own PST label.
 */
export const formatDatetimeWithTimezone = (dt: DateTime): string => {
  const formatted = dt.toLocaleString({ ...DateTime.DATETIME_FULL, timeZoneName: undefined })
  const isPCT =
    PACIFIC_ZONES.has(dt.zoneName ?? '') && dt.offset === -7 * 60 && (dt.toISODate() ?? '') >= PCT_START_DATE
  return `${formatted} ${isPCT ? 'PCT' : dt.offsetNameShort}`
}
