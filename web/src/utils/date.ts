import { DateTime } from 'luxon'

import { PST_UTC_OFFSET } from './constants'

export const isNoonInPST = (dt: string): boolean =>
  DateTime.fromISO(dt).setZone('UTC').hour === Math.abs(PST_UTC_OFFSET) + 12

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
