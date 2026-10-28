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
