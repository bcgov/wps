import moment from 'moment'

import { PST_UTC_OFFSET, PDT_UTC_OFFSET } from './constants'

export const isNoonInPST = (dt: string): boolean =>
  moment(dt)
    .utc()
    .hour() ===
  Math.abs(PST_UTC_OFFSET) + 12

export const formatDateInPST = (dt: string | number | Date, format?: string): string =>
  moment(dt)
    .utcOffset(PST_UTC_OFFSET)
    .format(format || 'YYYY-MM-DD HH:mm')

export const formatDateInPDT = (dt: string | number | Date, format?: string): string =>
  moment(dt)
    .utcOffset(PDT_UTC_OFFSET)
    .format(format || 'YYYY-MM-DD HH:mm')

export const formatMonthAndDay = (month: number, day: number): string =>
  moment()
    .month(month - 1)
    .date(day)
    .format('D MMMM')

export const formatDateInISO = (date: Date, format?: string): string =>
  moment(date).format(format || 'YYYY-MM-DDTHH:mm:ssZ')
