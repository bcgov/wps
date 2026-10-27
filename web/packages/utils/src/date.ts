import { isNull } from 'lodash'
import { DateTime } from 'luxon'
import { PDT_UTC_OFFSET, PST_ISO_TIMEZONE, PST_UTC_OFFSET } from './constants'

const UTC_NOON_HOUR = Math.abs(PST_UTC_OFFSET) + 12

export const isNoonInPST = (dt: string): boolean => DateTime.fromISO(dt).setZone('UTC').hour === UTC_NOON_HOUR

export const formatDatetimeInPST = (dt: string | Date | DateTime, format?: string): string => {
  let datetime: DateTime

  if (typeof dt === 'string') {
    datetime = DateTime.fromISO(dt)
  } else if (dt instanceof Date) {
    datetime = DateTime.fromJSDate(dt)
  } else {
    datetime = dt
  }

  return datetime.setZone(`UTC${PST_UTC_OFFSET}`).toFormat(format || 'yyyy-MM-dd HH:mm')
}

export const formatISODateInPST = (dateISOString: string): DateTime => {
  // Take a datetime ISO string, extract date ISO portion, set PST timezone and return as DateTime
  // E.g. 2021-08-02T20:00:00+00:00 becomes 2021-08-02T00:00-08:00
  return DateTime.fromISO(dateISOString.split('T')[0] + PST_ISO_TIMEZONE)
}

export const formatMonthAndDay = (month: number, day: number): string =>
  DateTime.fromObject({ month, day }).toFormat('d LLLL')

export const suppressMilliInISO = (iso: string): string => iso.replace(/\.\d{0,3}/, '') // Using RegExp to remove the "." and milliseconds

export const formatDateInUTC00Suffix = (dtISO: string): string => {
  // Given an ISO formated datetime string, return a ISO formatted datetime string for NOON UTC of that day.
  const dtDateTime = DateTime.fromISO(dtISO).setZone(`UTC${PST_UTC_OFFSET}`)
  const dtJS = dtDateTime.toJSDate()
  // We want today to stay today (e.g., if it's 11pm in PST, we know it's already tomorrow in UTC, but
  // we want the noon time for today in PST, not today in UTC, which is tomorrow. (today!)
  dtJS.setUTCDate(dtDateTime.day)
  dtJS.setUTCHours(UTC_NOON_HOUR)
  dtJS.setMinutes(0)
  dtJS.setSeconds(0)
  dtJS.setMilliseconds(0)
  const isoNoon = DateTime.fromJSDate(dtJS).setZone('UTC').toISO({ suppressMilliseconds: true, includeOffset: true })
  return `${isoNoon?.substring(0, isoNoon.length - 1)}+00:00`
}

export const pstFormatter = (fromDate: DateTime): string => {
  const pstFormattedDate = DateTime.fromObject(
    { year: fromDate.year, month: fromDate.month, day: fromDate.day },
    { zone: `UTC${PST_UTC_OFFSET}` }
  ).toISO()

  return !isNull(pstFormattedDate) ? pstFormattedDate : ''
}

export const getDateTimeNowPST = (): DateTime => {
  return DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`)
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

const PACIFIC_ZONES = new Set(['America/Vancouver', 'Canada/Pacific'])

/**
 * Formats a datetime in its own (usually the device's) timezone. Timezone data doesn't have a PCT abbreviation,
 * so Pacific times from Nov 1, 2026 are labelled PCT here instead of the PDT/MST the device would print. Devices
 * whose timezone data predates the switch still show UTC-8, so they keep their own PST label.
 */
export const formatDatetimeWithTimezone = (dt: DateTime): string => {
  const formatted = dt.toLocaleString({ ...DateTime.DATETIME_FULL, timeZoneName: undefined })
  const isPCT =
    PACIFIC_ZONES.has(dt.zoneName ?? '') &&
    dt.offset === PDT_UTC_OFFSET * 60 &&
    (dt.toISODate() ?? '') >= PCT_START_DATE
  return `${formatted} ${isPCT ? 'PCT' : dt.offsetNameShort}`
}
