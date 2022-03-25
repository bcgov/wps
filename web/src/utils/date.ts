import { DateTime, DurationLike, Interval } from 'luxon'

import { PST_ISO_TIMEZONE, PST_UTC_OFFSET } from './constants'

const UTC_NOON_HOUR = Math.abs(PST_UTC_OFFSET) + 12

export const toISO = (dtDateTime: DateTime): string => {
  // Use for consistent ISO formatting.
  return dtDateTime.toISO({ suppressMilliseconds: true, includeOffset: true })
}

export const isNoonInPST = (dt: string): boolean =>
  DateTime.fromISO(dt).setZone('UTC').hour === UTC_NOON_HOUR

export const formatDatetimeInPST = (
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

export const getDaysBetween = (startDate: string, endDate: string): DateTime[] => {
  const start = DateTime.fromISO(startDate)
  const end = DateTime.fromISO(endDate)
  const interval = Interval.fromDateTimes(start, end)

  if (interval.length('days') === 0) {
    return [start]
  }

  const dates = []

  let cursor = interval.start.startOf('day')
  while (cursor < interval.end) {
    dates.push(cursor)
    cursor = cursor.plus({ days: 1 })
  }

  return dates
}

export class SmartDate {
  /**
   * I propose we use a class that looks like this for all internal represenation of dates.
   * The idea is, that when dealing with this object, you never have to worry about
   * time zones.
   * We happen to represent the date internally using the luxon DateTime object,
   * but that's none of your business.
   */
  private _date: DateTime

  private constructor(date: DateTime) {
    this._date = date
  }

  static fromISODateString(isoDate: string): SmartDate {
    /* Given a date in the format YYYY-MM-DD return a smart date object.
    
    How we store the object is none of your business. */

    // setZone: true is very important here. We're telling DateTime not to use the local timezone,
    // and to just stick to the offset we've given it. This helps us avoid weird bugs where
    // converting to and fro between iso strings and date objects results in date changes due
    // to timezones. (e.g. the 14th of July in PST could be the 15th of July in UTC depending on
    // the time of day.)
    return new SmartDate(DateTime.fromISO(isoDate + 'T00:00+00:00', { setZone: true }))
  }

  static fromJSDate(jsDate: Date): SmartDate {
    /* Given a JS Date object return a smart date object - we don't care what timezone
    you're in, or what time it is. If you say it's June the 5th, you'll get June the 5th
    back. We throw away the time part of the date, and we throw away the timezone part.
    
    What we store it as internally is none of your business. */
    return SmartDate.fromISODateString(jsDate.toISOString().substring(0, 10))
  }

  public plus(duration: DurationLike): SmartDate {
    return new SmartDate(this._date.plus(duration))
  }

  public toISODateString(): string {
    /* Return an ISO date string in the format 'YYYY-MM-DD'.
    There is no time, or zone information - you asked for a date, and that's what you get.
    You get what you get and you don't get upset!
    */
    return this._date.toISODate()
  }
}
