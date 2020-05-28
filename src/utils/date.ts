import moment from 'moment'

import { PST_UTC_OFFSET, PDT_UTC_OFFSET } from 'utils/constants'

export const isNoonInPST = (dt: string) =>
  moment(dt)
    .utc()
    .hour() ===
  Math.abs(PST_UTC_OFFSET) + 12

export const datetimeInPDT = (dt: string | number, format?: string) =>
  moment(dt)
    .utcOffset(PDT_UTC_OFFSET)
    .format(format || 'YYYY-MM-DD HH:mm')
