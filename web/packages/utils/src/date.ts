import { isNull } from 'lodash'
import { DateTime } from 'luxon'
import { PACIFIC_IANA_TIMEZONE, PDT_UTC_OFFSET, PST_ISO_TIMEZONE, PST_UTC_OFFSET } from './constants'

const BC_PERMANENT_PACIFIC_START = DateTime.fromISO('2026-11-01T00:00:00-07:00').toMillis()

export const toBCPacificTime = (datetime: DateTime): DateTime => {
  // use a fixed offset after the change because browser timezone data can be out of date
  const zone = datetime.toMillis() >= BC_PERMANENT_PACIFIC_START ? `UTC${PDT_UTC_OFFSET}` : PACIFIC_IANA_TIMEZONE
  return datetime.setZone(zone)
}

export const formatISODateInPST = (dateISOString: string): DateTime => {
  // Take a datetime ISO string, extract date ISO portion, set PST timezone and return as DateTime
  // E.g. 2021-08-02T20:00:00+00:00 becomes 2021-08-02T00:00-08:00
  return DateTime.fromISO(dateISOString.split('T')[0] + PST_ISO_TIMEZONE)
}

export const formatMonthAndDay = (month: number, day: number): string =>
  DateTime.fromObject({ month, day }).toFormat('d LLLL')

export const suppressMilliInISO = (iso: string): string => iso.replace(/\.\d{0,3}/, '') // Using RegExp to remove the "." and milliseconds

export const pstFormatter = (fromDate: DateTime): string => {
  const pstFormattedDate = DateTime.fromObject(
    { year: fromDate.year, month: fromDate.month, day: fromDate.day },
    { zone: `UTC${PST_UTC_OFFSET}` }
  ).toISO()

  return !isNull(pstFormattedDate) ? pstFormattedDate : ''
}

export const getDateTimeNowPDT = (): DateTime => {
  return DateTime.now().setZone(`UTC${PDT_UTC_OFFSET}`)
}

// BC moved to permanent Pacific Time (UTC-7) on Nov 1, 2026; it's labelled PCT from then on instead of PDT.
const PCT_START_DATE = '2026-11-01'

/**
 * Label for UTC-7 BC time on the given ISO date. We don't rely on the device for this as it may be outside BC, in a
 * Mountain time part of BC, or have timezone data that predates BC's switch to permanent Pacific Time.
 */
export const getBCTimezoneLabel = (isoDate: string): string => (isoDate >= PCT_START_DATE ? 'PCT' : 'PDT')

/**
 * Formats a datetime in BC Pacific time with its timezone label, regardless of the device's timezone. The label is
 * hardcoded rather than taken from the device so it doesn't vary by locale (e.g. GMT-7 in en-GB, HAP in fr-CA).
 * Use formatDatetimeWithTimezone to show the device's own timezone instead.
 */
export const formatInBCPacificTime = (dt: DateTime, format: string): string => {
  const bcTime = toBCPacificTime(dt)
  const label = bcTime.offset === PDT_UTC_OFFSET * 60 ? getBCTimezoneLabel(bcTime.toISODate() ?? '') : 'PST'
  return `${bcTime.toFormat(format)} ${label}`
}

const PACIFIC_ZONES = new Set(['America/Vancouver', 'Canada/Pacific'])

/**
 * Formats a datetime in its own (usually the device's) timezone. Timezone data doesn't have a PCT abbreviation,
 * so Pacific times from Nov 1, 2026 are labelled PCT here instead of the PDT/MST the device would print. Devices
 * whose timezone data predates the switch still show UTC-8, so they keep their own PST label.
 * Use formatInBCPacificTime to always show BC time instead.
 */
export const formatDatetimeWithTimezone = (dt: DateTime): string => {
  const formatted = dt.toLocaleString({ ...DateTime.DATETIME_FULL, timeZoneName: undefined })
  const isPCT =
    PACIFIC_ZONES.has(dt.zoneName ?? '') &&
    dt.offset === PDT_UTC_OFFSET * 60 &&
    (dt.toISODate() ?? '') >= PCT_START_DATE
  return `${formatted} ${isPCT ? 'PCT' : dt.offsetNameShort}`
}
