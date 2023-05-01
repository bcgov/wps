import { DateTime } from 'luxon'

import { PST_ISO_TIMEZONE, PST_UTC_OFFSET } from './constants'

const UTC_NOON_HOUR = Math.abs(PST_UTC_OFFSET) + 12

export const toISO = (dtDateTime: DateTime): string => {
  // Use for consistent ISO formatting.
  return dtDateTime.toISO({ suppressMilliseconds: true, includeOffset: true })
}

export const isNoonInPST = (dt: string): boolean => DateTime.fromISO(dt).setZone('UTC').hour === UTC_NOON_HOUR

export const formatDatetimeInPST = (dt: string | Date | DateTime, format?: string): string => {
  let datetime = undefined

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
  const isoNoon = toISO(DateTime.fromJSDate(dtJS).setZone('UTC'))
  return isoNoon.substring(0, isoNoon.length - 1) + '+00:00'
}

export const pstFormatter = (fromDate: DateTime): string => {
  return DateTime.fromObject(
    { year: fromDate.year, month: fromDate.month, day: fromDate.day },
    { zone: `UTC${PST_UTC_OFFSET}` }
  ).toISO()
}
