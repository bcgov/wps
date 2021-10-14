import { DateTime } from 'luxon'

import { PST_UTC_OFFSET } from './constants'

const UTC_NOON_HOUR = Math.abs(PST_UTC_OFFSET) + 12

const toISO = (dtDateTime: DateTime): string => {
  // Use for consistent ISO formatting.
  return dtDateTime.toISO({ suppressMilliseconds: true, includeOffset: true })
}

export const isNoonInPST = (dt: string): boolean =>
  DateTime.fromISO(dt).setZone('UTC').hour === UTC_NOON_HOUR

export const formatDateInPST = (
  dt: string | Date | DateTime,
  format?: string
): string => {
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

export const getPrepWeeklyDateRange = (
  dateOfInterest: string
): { start: DateTime; end: DateTime } => {
  const day = DateTime.fromISO(dateOfInterest).weekday
  let dayOffset = 0
  switch (day) {
    case 2: // Tuesday
      dayOffset = 1
      break
    case 3: // Wednesday
      dayOffset = 2
      break
    case 5: // Friday
      dayOffset = 1
      break
    case 6: // Saturday
      dayOffset = 2
      break
    case 7: // Sunday
      dayOffset = 3
  }
  const start = DateTime.fromISO(dateOfInterest).minus({ days: dayOffset }).startOf('day')
  const end = DateTime.fromISO(dateOfInterest)
    .minus({ days: dayOffset })
    .endOf('day')
    .plus({ days: 4 })
  return { start, end }
}

export const getPrepDailyDateRange = (
  dateOfInterest: string
): { start: DateTime; end: DateTime } => {
  const start = DateTime.fromISO(dateOfInterest).startOf('day')
  const end = DateTime.fromISO(dateOfInterest).endOf('day')

  return { start, end }
}

export const getDateRange = (
  isWeeklyView: boolean,
  dateOfInterest: string
): { start: DateTime; end: DateTime } => {
  return isWeeklyView
    ? getPrepWeeklyDateRange(dateOfInterest)
    : getPrepDailyDateRange(dateOfInterest)
}
