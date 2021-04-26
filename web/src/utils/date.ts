import { noonModelTableColumns } from 'features/fireWeather/components/tables/NoonWxValueTables'
import { DateTime, FixedOffsetZone } from 'luxon'

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

export const reformatDate = (dtISO: string): string => {
  // Take an ISO formatted datetime string, and re-format it into UTC ISO formatted datetime.
  // This is especially useful, as there is more than one way of representing the same UTC formatted ISO
  // date!
  return toISO(DateTime.fromISO(dtISO).setZone('UTC'))
}

export const getNoonDate = (dtISO: string): string => {
  // Given an ISO formated datetime string, return a ISO formatted datetime string for NOON UTC of that day.
  const dtDateTime = DateTime.fromISO(dtISO).setZone('UTC')
  const dtJS = dtDateTime.toJSDate()
  dtJS.setUTCHours(UTC_NOON_HOUR)
  dtJS.setMinutes(0)
  dtJS.setSeconds(0)
  dtJS.setMilliseconds(0)
  return toISO(DateTime.fromJSDate(dtJS).setZone('UTC'))
}
